package npm

import (
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"regexp"
	"strings"
	"time"

	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/types"
)

// NPMTool implements the Tool interface for NPM global package management
type NPMTool struct {
	config *config.NPMConfig
	dryRun bool
}

// NPMPackageInfo represents information about an NPM package
type NPMPackageInfo struct {
	Name            string `json:"name"`
	Version         string `json:"version"`
	LatestVersion   string `json:"latest_version,omitempty"`
	UpdateAvailable bool   `json:"update_available"`
}

// NewNPMTool creates a new NPMTool instance
func NewNPMTool(cfg *config.Config) *NPMTool {
	return &NPMTool{
		config: &cfg.NPM,
		dryRun: cfg.Global.DryRun,
	}
}

// Name returns the tool name
func (n *NPMTool) Name() string {
	return "npm"
}

// IsEnabled returns whether the tool is enabled
func (n *NPMTool) IsEnabled() bool {
	return n.config != nil
}

// Priority returns the tool priority
func (n *NPMTool) Priority() int {
	return 50 // Run after apps
}

// Validate checks if npm is available and packages are valid
func (n *NPMTool) Validate() error {
	// Check if npm command is available
	if _, err := exec.LookPath("npm"); err != nil {
		return fmt.Errorf("npm command not found: %w", err)
	}

	// Check if Node.js is available
	if _, err := exec.LookPath("node"); err != nil {
		return fmt.Errorf("node command not found: %w", err)
	}

	// Validate package names (basic validation)
	packageNameRegex := regexp.MustCompile(`^(@[a-z0-9-~][a-z0-9-._~]*\/)?[a-z0-9-~][a-z0-9-._~]*$`)
	for _, packageName := range n.config.GlobalPackages {
		if !packageNameRegex.MatchString(packageName) {
			return fmt.Errorf("invalid package name: %s", packageName)
		}
	}

	return nil
}

// Status returns the current status of npm global packages
func (n *NPMTool) Status(ctx context.Context) (*types.ToolStatus, error) {
	status := &types.ToolStatus{
		Name:      n.Name(),
		Enabled:   n.IsEnabled(),
		Healthy:   true,
		LastCheck: time.Now(),
		Items:     make([]types.ToolItem, 0),
	}

	if !n.IsEnabled() {
		return status, nil
	}

	installedPackages, err := n.getInstalledPackages()
	if err != nil {
		status.Healthy = false
		status.Error = err
		return status, nil
	}

	for _, packageName := range n.config.GlobalPackages {
		item := types.ToolItem{
			Name:        packageName,
			Description: "NPM global package",
			Enabled:     true,
		}

		if installedPkg, exists := installedPackages[packageName]; exists {
			item.Status = "installed"
			item.Version = installedPkg.Version
			item.Description = fmt.Sprintf("NPM global package (v%s)", installedPkg.Version)

			// Check for updates if auto_update is enabled
			if n.config.AutoUpdate {
				latestVersion, err := n.getLatestVersion(packageName)
				if err == nil && latestVersion != installedPkg.Version {
					item.Status = "update_available"
					item.Description = fmt.Sprintf("NPM global package (v%s → v%s)", installedPkg.Version, latestVersion)
				}
			}
		} else {
			item.Status = "not_installed"
		}

		status.Items = append(status.Items, item)
	}

	return status, nil
}

// Install installs specified NPM packages globally
func (n *NPMTool) Install(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      n.Name(),
		Operation: "install",
		Success:   true,
		Details:   make(map[string]interface{}),
	}

	var errors []string
	var installed []string

	// If no specific items provided, install all configured packages
	packages := items
	if len(packages) == 0 {
		packages = n.config.GlobalPackages
	}

	for _, packageName := range packages {
		if err := n.installPackage(packageName); err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", packageName, err))
			result.Success = false
		} else {
			installed = append(installed, packageName)
		}
	}

	result.Details["installed"] = installed
	result.Details["errors"] = errors

	if len(errors) > 0 {
		result.Error = fmt.Errorf("failed to install some packages: %s", strings.Join(errors, "; "))
	}

	return result, nil
}

// Update updates specified NPM packages or all if none specified
func (n *NPMTool) Update(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      n.Name(),
		Operation: "update",
		Success:   true,
		Details:   make(map[string]interface{}),
	}

	var errors []string
	var updated []string

	packages := items
	if len(packages) == 0 {
		packages = n.config.GlobalPackages
	}

	for _, packageName := range packages {
		if err := n.updatePackage(packageName); err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", packageName, err))
			result.Success = false
		} else {
			updated = append(updated, packageName)
		}
	}

	result.Details["updated"] = updated
	result.Details["errors"] = errors

	if len(errors) > 0 {
		result.Error = fmt.Errorf("failed to update some packages: %s", strings.Join(errors, "; "))
	}

	return result, nil
}

// Remove removes specified NPM packages
func (n *NPMTool) Remove(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      n.Name(),
		Operation: "remove",
		Success:   true,
		Details:   make(map[string]interface{}),
	}

	var errors []string
	var removed []string

	for _, packageName := range items {
		if err := n.removePackage(packageName); err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", packageName, err))
			result.Success = false
		} else {
			removed = append(removed, packageName)
		}
	}

	result.Details["removed"] = removed
	result.Details["errors"] = errors

	if len(errors) > 0 {
		result.Error = fmt.Errorf("failed to remove some packages: %s", strings.Join(errors, "; "))
	}

	return result, nil
}

// List returns all configured NPM packages
func (n *NPMTool) List(ctx context.Context) ([]types.ToolItem, error) {
	status, err := n.Status(ctx)
	if err != nil {
		return nil, err
	}
	return status.Items, nil
}

// Sync installs all configured packages if auto_install is enabled
func (n *NPMTool) Sync(ctx context.Context) (*types.OperationResult, error) {
	if n.config.AutoInstall {
		return n.Install(ctx, nil)
	}

	// If auto_install is disabled, just return success without doing anything
	return &types.OperationResult{
		Tool:      n.Name(),
		Operation: "sync",
		Success:   true,
		Details:   map[string]interface{}{"message": "auto_install disabled"},
	}, nil
}

// Configure updates the tool configuration
func (n *NPMTool) Configure(cfg interface{}) error {
	config, ok := cfg.(*config.NPMConfig)
	if !ok {
		return fmt.Errorf("invalid configuration type for npm tool")
	}
	n.config = config
	return nil
}

// Helper methods

func (n *NPMTool) installPackage(packageName string) error {
	args := []string{"install", "-g", packageName}
	if n.dryRun {
		// npm doesn't have a built-in dry-run, so we'll just simulate it
		return nil
	}

	cmd := exec.Command("npm", args...)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("npm install failed: %w\nOutput: %s", err, string(output))
	}

	return nil
}

func (n *NPMTool) updatePackage(packageName string) error {
	args := []string{"update", "-g", packageName}
	if n.dryRun {
		return nil
	}

	cmd := exec.Command("npm", args...)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("npm update failed: %w\nOutput: %s", err, string(output))
	}

	return nil
}

func (n *NPMTool) removePackage(packageName string) error {
	args := []string{"uninstall", "-g", packageName}
	if n.dryRun {
		return nil
	}

	cmd := exec.Command("npm", args...)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("npm uninstall failed: %w\nOutput: %s", err, string(output))
	}

	return nil
}

func (n *NPMTool) getInstalledPackages() (map[string]NPMPackageInfo, error) {
	cmd := exec.Command("npm", "list", "-g", "--depth=0", "--json")
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to list npm packages: %w", err)
	}

	var listResult struct {
		Dependencies map[string]struct {
			Version string `json:"version"`
		} `json:"dependencies"`
	}

	if err := json.Unmarshal(output, &listResult); err != nil {
		return nil, fmt.Errorf("failed to parse npm list output: %w", err)
	}

	packages := make(map[string]NPMPackageInfo)
	for name, info := range listResult.Dependencies {
		packages[name] = NPMPackageInfo{
			Name:    name,
			Version: info.Version,
		}
	}

	return packages, nil
}

func (n *NPMTool) getLatestVersion(packageName string) (string, error) {
	cmd := exec.Command("npm", "view", packageName, "version")
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("failed to get latest version for %s: %w", packageName, err)
	}

	version := strings.TrimSpace(string(output))
	return version, nil
}
