package homebrew

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/yourusername/dotfiles/internal/config"
	"github.com/yourusername/dotfiles/internal/types"
)

// HomebrewTool implements the Tool interface for Homebrew package management
type HomebrewTool struct {
	config       *config.HomebrewConfig
	dotfilesPath string
	dryRun       bool
}

// BrewPackage represents a package from brew list output
type BrewPackage struct {
	Name    string `json:"name"`
	Version string `json:"version"`
	Type    string `json:"type"` // formula, cask, etc.
}

// NewHomebrewTool creates a new HomebrewTool instance
func NewHomebrewTool(cfg *config.Config) *HomebrewTool {
	return &HomebrewTool{
		config:       &cfg.Homebrew,
		dotfilesPath: cfg.Global.DotfilesPath,
		dryRun:       cfg.Global.DryRun,
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

// Priority returns the tool priority
func (h *HomebrewTool) Priority() int {
	return 30 // Run after stow and rsync
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
			return fmt.Errorf("Brewfile for category %s not found: %s", name, brewfilePath)
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
					} else {
						item.Status = "partial"
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
		return fmt.Errorf("Brewfile not found: %s", brewfilePath)
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
		if strings.HasPrefix(line, "brew ") || strings.HasPrefix(line, "cask ") || strings.HasPrefix(line, "mas ") {
			total++
		}
	}

	// Get installed packages
	installedPackages, err := h.getInstalledPackages()
	if err != nil {
		return total, 0, fmt.Errorf("failed to get installed packages: %w", err)
	}

	// Count how many packages from Brewfile are installed
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "brew ") || strings.HasPrefix(line, "cask ") {
			// Extract package name (simplified parsing)
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				packageName := strings.Trim(parts[1], "\"'")
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
	// Get formulae
	cmd := exec.Command("brew", "list", "--formula", "--json=v1")
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to list formulae: %w", err)
	}

	var formulae []BrewPackage
	if err := json.Unmarshal(output, &formulae); err != nil {
		return nil, fmt.Errorf("failed to parse formulae JSON: %w", err)
	}

	// Get casks
	cmd = exec.Command("brew", "list", "--cask", "--json=v1")
	output, err = cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to list casks: %w", err)
	}

	var casks []BrewPackage
	if err := json.Unmarshal(output, &casks); err != nil {
		return nil, fmt.Errorf("failed to parse casks JSON: %w", err)
	}

	// Combine results
	packages := make([]BrewPackage, 0, len(formulae)+len(casks))
	packages = append(packages, formulae...)
	packages = append(packages, casks...)

	return packages, nil
}