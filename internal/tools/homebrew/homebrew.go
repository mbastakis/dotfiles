package homebrew

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/types"
)

// HomebrewTool implements the Tool interface for Homebrew package management
type HomebrewTool struct {
	config       *config.HomebrewConfig
	dotfilesPath string
	dryRun       bool
	priority     int
}

// BrewPackage represents a package from brew list output
type BrewPackage struct {
	Name    string `json:"name"`
	Version string `json:"version"`
	Type    string `json:"type"` // formula, cask, etc.
}

// NewHomebrewTool creates a new HomebrewTool instance
func NewHomebrewTool(cfg *config.Config) *HomebrewTool {
	priority := 30 // default fallback
	if p, exists := cfg.Tools.Priorities["homebrew"]; exists {
		priority = p
	}
	
	return &HomebrewTool{
		config:       &cfg.Homebrew,
		dotfilesPath: cfg.Global.DotfilesPath,
		dryRun:       cfg.Global.DryRun,
		priority:     priority,
	}
}

// Name returns the tool name
func (h *HomebrewTool) Name() string {
	return "homebrew"
}

// IsEnabled returns whether the tool is enabled
func (h *HomebrewTool) IsEnabled() bool {
	return h.config != nil
}

// Priority returns the tool priority (configurable)
func (h *HomebrewTool) Priority() int {
	return h.priority
}

// Validate checks if brew is available and Brewfiles exist
func (h *HomebrewTool) Validate() error {
	// Check if brew command is available
	if _, err := exec.LookPath("brew"); err != nil {
		return fmt.Errorf("brew command not found: %w", err)
	}

	// Validate Brewfiles exist for enabled categories
	for name, category := range h.config.Categories {
		if !category.Enabled {
			continue
		}

		brewfilePath := filepath.Join(h.dotfilesPath, category.Brewfile)
		if _, err := os.Stat(brewfilePath); err != nil {
			return fmt.Errorf("brewfile for category %s not found: %s", name, brewfilePath)
		}
	}

	return nil
}

// Status returns the current status of homebrew categories
func (h *HomebrewTool) Status(ctx context.Context) (*types.ToolStatus, error) {
	status := &types.ToolStatus{
		Name:      h.Name(),
		Enabled:   h.IsEnabled(),
		Healthy:   true,
		LastCheck: time.Now(),
		Items:     make([]types.ToolItem, 0),
	}

	if !h.IsEnabled() {
		return status, nil
	}

	for name, category := range h.config.Categories {
		item := types.ToolItem{
			Name:        name,
			Description: fmt.Sprintf("Brewfile: %s", category.Brewfile),
			Enabled:     category.Enabled,
		}

		if !category.Enabled {
			item.Status = "disabled"
		} else {
			// Check if Brewfile exists and get package count
			brewfilePath := filepath.Join(h.dotfilesPath, category.Brewfile)
			if _, err := os.Stat(brewfilePath); err != nil {
				item.Status = "error"
				item.Error = fmt.Sprintf("Brewfile not found: %s", brewfilePath)
			} else {
				packageCount, installedCount, err := h.getBrewfileStatus(brewfilePath)
				if err != nil {
					item.Status = "error"
					item.Error = err.Error()
				} else {
					if installedCount == packageCount {
						item.Status = "installed"
						item.Installed = true
					} else {
						item.Status = "partial"
						item.Installed = false
					}
					item.Description = fmt.Sprintf("%s (%d/%d packages)", item.Description, installedCount, packageCount)
				}
			}
		}

		status.Items = append(status.Items, item)
	}

	return status, nil
}

// Install installs packages from specified categories
func (h *HomebrewTool) Install(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      h.Name(),
		Operation: "install",
		Success:   true,
		Details:   make(map[string]interface{}),
	}

	var errors []string
	var installed []string

	// If no specific items provided, install all enabled categories
	if len(items) == 0 {
		for name, category := range h.config.Categories {
			if category.Enabled {
				items = append(items, name)
			}
		}
	}

	for _, categoryName := range items {
		if err := h.installCategory(categoryName); err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", categoryName, err))
			result.Success = false
		} else {
			installed = append(installed, categoryName)
		}
	}

	result.Details["installed"] = installed
	result.Details["errors"] = errors

	if len(errors) > 0 {
		result.Error = fmt.Errorf("failed to install some categories: %s", strings.Join(errors, "; "))
	}

	return result, nil
}

// Update updates all installed packages
func (h *HomebrewTool) Update(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      h.Name(),
		Operation: "update",
		Success:   true,
		Details:   make(map[string]interface{}),
	}

	// Update brew itself first if auto_update is enabled
	if h.config.AutoUpdate {
		if err := h.runBrewCommand("update"); err != nil {
			result.Success = false
			result.Error = fmt.Errorf("failed to update brew: %w", err)
			return result, nil
		}
	}

	// Upgrade all packages
	if err := h.runBrewCommand("upgrade"); err != nil {
		result.Success = false
		result.Error = fmt.Errorf("failed to upgrade packages: %w", err)
		return result, nil
	}

	result.Details["updated"] = "all packages"
	return result, nil
}

// Remove removes packages (not typically used for Homebrew in dotfiles context)
func (h *HomebrewTool) Remove(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      h.Name(),
		Operation: "remove",
		Success:   true,
		Details:   make(map[string]interface{}),
	}

	// For homebrew, we don't typically remove individual packages
	// Instead, we might cleanup orphaned packages
	if err := h.runBrewCommand("cleanup"); err != nil {
		result.Success = false
		result.Error = fmt.Errorf("failed to cleanup: %w", err)
		return result, nil
	}

	result.Details["cleaned"] = true
	return result, nil
}

// List returns all configured homebrew categories
func (h *HomebrewTool) List(ctx context.Context) ([]types.ToolItem, error) {
	status, err := h.Status(ctx)
	if err != nil {
		return nil, err
	}
	return status.Items, nil
}

// Sync installs all enabled categories
func (h *HomebrewTool) Sync(ctx context.Context) (*types.OperationResult, error) {
	return h.Install(ctx, nil)
}

// Configure updates the tool configuration
func (h *HomebrewTool) Configure(cfg interface{}) error {
	config, ok := cfg.(*config.HomebrewConfig)
	if !ok {
		return fmt.Errorf("invalid configuration type for homebrew tool")
	}
	h.config = config
	return nil
}

// Helper methods

func (h *HomebrewTool) installCategory(categoryName string) error {
	category, exists := h.config.Categories[categoryName]
	if !exists {
		return fmt.Errorf("category %s not found", categoryName)
	}

	if !category.Enabled {
		return fmt.Errorf("category %s is disabled", categoryName)
	}

	brewfilePath := filepath.Join(h.dotfilesPath, category.Brewfile)
	if _, err := os.Stat(brewfilePath); err != nil {
		return fmt.Errorf("brewfile not found: %s", brewfilePath)
	}

	// Run brew bundle
	args := []string{"bundle", "--file", brewfilePath}
	if h.dryRun {
		args = append(args, "--dry-run")
	}

	cmd := exec.Command("brew", args...)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("brew bundle failed: %w\nOutput: %s", err, string(output))
	}

	return nil
}

func (h *HomebrewTool) runBrewCommand(subcommand string, args ...string) error {
	cmdArgs := append([]string{subcommand}, args...)
	if h.dryRun {
		cmdArgs = append(cmdArgs, "--dry-run")
	}

	cmd := exec.Command("brew", cmdArgs...)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("brew %s failed: %w\nOutput: %s", subcommand, err, string(output))
	}

	return nil
}

func (h *HomebrewTool) getBrewfileStatus(brewfilePath string) (total, installed int, err error) {
	// Read Brewfile to count total packages
	content, err := os.ReadFile(brewfilePath)
	if err != nil {
		return 0, 0, fmt.Errorf("failed to read Brewfile: %w", err)
	}

	lines := strings.Split(string(content), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "brew ") || strings.HasPrefix(line, "cask ") || strings.HasPrefix(line, "mas ") || strings.HasPrefix(line, "tap ") {
			total++
		}
	}

	// Get installed packages
	installedPackages, err := h.getInstalledPackages()
	if err != nil {
		return total, 0, fmt.Errorf("failed to get installed packages: %w", err)
	}

	// Get installed taps
	installedTaps, err := h.getInstalledTaps()
	if err != nil {
		return total, 0, fmt.Errorf("failed to get installed taps: %w", err)
	}

	// Count how many packages from Brewfile are installed
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "brew ") || strings.HasPrefix(line, "cask ") || strings.HasPrefix(line, "mas ") || strings.HasPrefix(line, "tap ") {
			// Extract package name - handle quoted names and comments
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				packageName := parts[1]
				// Remove quotes
				packageName = strings.Trim(packageName, "\"'")
				// Remove any trailing comments or extra characters
				if commentIdx := strings.Index(packageName, "#"); commentIdx >= 0 {
					packageName = strings.TrimSpace(packageName[:commentIdx])
				}

				// For mas entries, check if they're actually installed
				if strings.HasPrefix(line, "mas ") {
					masInstalled, err := h.isMasAppInstalled(packageName, line)
					if err == nil && masInstalled {
						installed++
					}
					continue
				}

				// Check if this is a tap
				if strings.HasPrefix(line, "tap ") {
					for _, tap := range installedTaps {
						if tap == packageName {
							installed++
							break
						}
					}
					continue
				}

				// Check for regular packages
				for _, pkg := range installedPackages {
					if pkg.Name == packageName {
						installed++
						break
					}
				}
			}
		}
	}

	return total, installed, nil
}

func (h *HomebrewTool) getInstalledPackages() ([]BrewPackage, error) {
	var packages []BrewPackage

	// Get formulae
	cmd := exec.Command("brew", "list", "--formula")
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to list formulae: %w", err)
	}

	// Parse formulae output (one package per line)
	formulaeLines := strings.Split(strings.TrimSpace(string(output)), "\n")
	for _, line := range formulaeLines {
		line = strings.TrimSpace(line)
		if line != "" {
			packages = append(packages, BrewPackage{
				Name: line,
				Type: "brew", // Use "brew" to match our package type
			})
		}
	}

	// Get casks
	cmd = exec.Command("brew", "list", "--cask")
	output, err = cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to list casks: %w", err)
	}

	// Parse casks output (one package per line)
	caskLines := strings.Split(strings.TrimSpace(string(output)), "\n")
	for _, line := range caskLines {
		line = strings.TrimSpace(line)
		if line != "" {
			packages = append(packages, BrewPackage{
				Name: line,
				Type: "cask",
			})
		}
	}

	return packages, nil
}

// CategoryTool interface implementation

// SupportsCategories returns true for homebrew tool
func (h *HomebrewTool) SupportsCategories() bool {
	return true
}

// ListCategoryItems returns all packages in a specific category
func (h *HomebrewTool) ListCategoryItems(ctx context.Context, category string) ([]types.ToolItem, error) {
	categoryConfig, exists := h.config.Categories[category]
	if !exists {
		return nil, fmt.Errorf("category %s not found", category)
	}

	if !categoryConfig.Enabled {
		return nil, fmt.Errorf("category %s is disabled", category)
	}

	brewfilePath := filepath.Join(h.dotfilesPath, categoryConfig.Brewfile)
	if _, err := os.Stat(brewfilePath); err != nil {
		return nil, fmt.Errorf("brewfile not found: %s", brewfilePath)
	}

	return h.parseBrewfilePackages(brewfilePath, category)
}

// InstallCategoryItem installs a specific package from a category
func (h *HomebrewTool) InstallCategoryItem(ctx context.Context, category string, item string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      h.Name(),
		Operation: "install_package",
		Success:   true,
		Message:   fmt.Sprintf("Package %s installed successfully", item),
	}

	// Get the package details first to determine type
	packages, err := h.ListCategoryItems(ctx, category)
	if err != nil {
		result.Success = false
		result.Error = err
		return result, err
	}

	var targetPackage *types.ToolItem
	for _, pkg := range packages {
		if pkg.Name == item {
			targetPackage = &pkg
			break
		}
	}

	if targetPackage == nil {
		result.Success = false
		result.Error = fmt.Errorf("package %s not found in category %s", item, category)
		return result, result.Error
	}

	// Install the package based on its type
	if err := h.installSinglePackage(targetPackage.Name, targetPackage.PackageType); err != nil {
		result.Success = false
		result.Error = err
		result.Message = fmt.Sprintf("Failed to install package %s: %v", item, err)
		return result, err
	}

	result.Modified = []string{item}
	return result, nil
}

// parseBrewfilePackages parses a Brewfile and returns individual packages as ToolItems
func (h *HomebrewTool) parseBrewfilePackages(brewfilePath, category string) ([]types.ToolItem, error) {
	content, err := os.ReadFile(brewfilePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read Brewfile: %w", err)
	}

	var packages []types.ToolItem
	lines := strings.Split(string(content), "\n")

	// Get installed packages for status checking
	installedPackages, err := h.getInstalledPackages()
	if err != nil {
		// Continue without status checking if we can't get installed packages
		installedPackages = []BrewPackage{}
	}

	// Get installed taps for status checking
	installedTaps, err := h.getInstalledTaps()
	if err != nil {
		// Continue without status checking if we can't get installed taps
		installedTaps = []string{}
	}

	for lineNum, line := range lines {
		line = strings.TrimSpace(line)

		// Skip comments and empty lines
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		var packageType, packageName, description string

		// Parse different types of package declarations
		if strings.HasPrefix(line, "brew ") {
			packageType = "brew"
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				packageName = strings.Trim(parts[1], "\"'")
			}
		} else if strings.HasPrefix(line, "cask ") {
			packageType = "cask"
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				packageName = strings.Trim(parts[1], "\"'")
			}
		} else if strings.HasPrefix(line, "mas ") {
			packageType = "mas"
			// For mas entries, extract the app name from quotes
			// Format: mas "App Name", id: 123456789
			quoteStart := strings.Index(line, "\"")
			if quoteStart >= 0 {
				remaining := line[quoteStart+1:]
				quoteEnd := strings.Index(remaining, "\"")
				if quoteEnd >= 0 {
					packageName = remaining[:quoteEnd]
				}
			}
		} else if strings.HasPrefix(line, "tap ") {
			packageType = "tap"
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				packageName = strings.Trim(parts[1], "\"'")
			}
		} else {
			// Skip lines that don't match known patterns
			continue
		}

		if packageName == "" {
			continue
		}

		// Extract description from comment
		if commentIdx := strings.Index(line, "#"); commentIdx >= 0 {
			description = strings.TrimSpace(line[commentIdx+1:])
		}

		// Determine installation status
		var installed bool
		status := "not_installed"

		if packageType == "tap" {
			installed = h.isTapInstalled(packageName, installedTaps)
		} else {
			installed = h.isPackageInstalled(packageName, packageType, installedPackages)
		}

		if installed {
			status = "installed"
		}

		// For mas packages, check if they're installed using mas CLI
		if packageType == "mas" {
			// Try to get the app ID from the mas line and check if installed
			masInstalled, err := h.isMasAppInstalled(packageName, line)
			if err != nil {
				status = "unknown"
				installed = false
			} else {
				installed = masInstalled
				if installed {
					status = "installed"
				} else {
					status = "not_installed"
				}
			}
		}

		pkg := types.ToolItem{
			Name:        packageName,
			Description: description,
			Status:      status,
			Enabled:     true,
			Installed:   installed,
			Category:    category,
			PackageType: packageType,
			Priority:    lineNum, // Use line number as priority for ordering
		}

		packages = append(packages, pkg)
	}

	return packages, nil
}

// isPackageInstalled checks if a specific package is installed
func (h *HomebrewTool) isPackageInstalled(packageName, packageType string, installedPackages []BrewPackage) bool {
	for _, pkg := range installedPackages {
		if pkg.Name == packageName && pkg.Type == packageType {
			return true
		}
	}
	return false
}

// getInstalledTaps returns a list of currently installed Homebrew taps
func (h *HomebrewTool) getInstalledTaps() ([]string, error) {
	cmd := exec.Command("brew", "tap")
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to list taps: %w", err)
	}

	// Parse taps output (one tap per line)
	tapLines := strings.Split(strings.TrimSpace(string(output)), "\n")
	var taps []string
	for _, line := range tapLines {
		line = strings.TrimSpace(line)
		if line != "" {
			taps = append(taps, line)
		}
	}

	return taps, nil
}

// isTapInstalled checks if a specific tap is installed
func (h *HomebrewTool) isTapInstalled(tapName string, installedTaps []string) bool {
	for _, tap := range installedTaps {
		if tap == tapName {
			return true
		}
	}
	return false
}

// isMasAppInstalled checks if a MAS app is installed by extracting the app ID from the mas line
func (h *HomebrewTool) isMasAppInstalled(appName, masLine string) (bool, error) {
	// Extract app ID from mas line format: mas "App Name", id: 123456789
	idIdx := strings.Index(masLine, "id:")
	if idIdx == -1 {
		return false, fmt.Errorf("unable to find app ID in mas line: %s", masLine)
	}

	// Extract the ID part after "id:"
	idPart := strings.TrimSpace(masLine[idIdx+3:])
	// Remove any trailing comments
	if commentIdx := strings.Index(idPart, "#"); commentIdx >= 0 {
		idPart = strings.TrimSpace(idPart[:commentIdx])
	}

	appID := strings.TrimSpace(idPart)

	// Get installed MAS apps
	cmd := exec.Command("mas", "list")
	output, err := cmd.Output()
	if err != nil {
		return false, fmt.Errorf("failed to list mas apps: %w", err)
	}

	// Check if the app ID is in the output
	outputStr := string(output)
	return strings.Contains(outputStr, appID), nil
}

// installSinglePackage installs a single package based on its type
func (h *HomebrewTool) installSinglePackage(packageName, packageType string) error {
	var args []string

	switch packageType {
	case "brew":
		args = []string{"install", packageName}
	case "cask":
		args = []string{"install", "--cask", packageName}
	case "mas":
		// For mas packages, we need to use mas CLI with the app ID
		// Extract app ID from the package info - this would need to be passed differently
		return fmt.Errorf("mas package installation requires app ID - please use 'mas install <id>' manually")
	case "tap":
		args = []string{"tap", packageName}
	default:
		return fmt.Errorf("unknown package type: %s", packageType)
	}

	if h.dryRun {
		args = append([]string{"--dry-run"}, args...)
	}

	cmd := exec.Command("brew", args...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("brew install failed: %w\nOutput: %s", err, string(output))
	}

	return nil
}
