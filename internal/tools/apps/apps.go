package apps

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

// AppsTool implements the Tool interface for custom application script execution
type AppsTool struct {
	config       *config.AppsConfig
	dotfilesPath string
	dryRun       bool
	priority     int
	interpreters map[string]string
}

// NewAppsTool creates a new AppsTool instance
func NewAppsTool(cfg *config.Config) *AppsTool {
	priority := 40 // default fallback
	if p, exists := cfg.Tools.Priorities["apps"]; exists {
		priority = p
	}

	return &AppsTool{
		config:       &cfg.Apps,
		dotfilesPath: cfg.Global.DotfilesPath,
		dryRun:       cfg.Global.DryRun,
		priority:     priority,
		interpreters: cfg.Tools.Interpreters,
	}
}

// Name returns the tool name
func (a *AppsTool) Name() string {
	return "apps"
}

// IsEnabled returns whether the tool is enabled
func (a *AppsTool) IsEnabled() bool {
	return a.config != nil && len(*a.config) > 0
}

// Priority returns the tool priority (configurable)
func (a *AppsTool) Priority() int {
	return a.priority
}

// Validate checks if all app scripts exist and are executable
func (a *AppsTool) Validate() error {
	for appName, appConfig := range *a.config {
		if !appConfig.Enabled {
			continue
		}

		for _, scriptPath := range appConfig.Scripts {
			fullPath := a.resolveScriptPath(scriptPath)

			// Check if script exists
			if _, err := os.Stat(fullPath); err != nil {
				return fmt.Errorf("script %s for app %s not found: %w", fullPath, appName, err)
			}

			// Check if script is executable
			info, err := os.Stat(fullPath)
			if err != nil {
				return fmt.Errorf("failed to check script %s: %w", fullPath, err)
			}

			if info.Mode()&0111 == 0 {
				return fmt.Errorf("script %s is not executable", fullPath)
			}
		}
	}

	return nil
}

// Status returns the current status of apps
func (a *AppsTool) Status(ctx context.Context) (*types.ToolStatus, error) {
	status := &types.ToolStatus{
		Name:      a.Name(),
		Enabled:   a.IsEnabled(),
		Healthy:   true,
		LastCheck: time.Now(),
		Items:     make([]types.ToolItem, 0),
	}

	if !a.IsEnabled() {
		return status, nil
	}

	for appName, appConfig := range *a.config {
		item := types.ToolItem{
			Name:        appName,
			Description: fmt.Sprintf("Custom app with %d scripts", len(appConfig.Scripts)),
			Enabled:     appConfig.Enabled,
		}

		if !appConfig.Enabled {
			item.Status = "disabled"
		} else {
			// Check if all scripts exist and are executable
			allScriptsValid := true
			var invalidScripts []string

			for _, scriptPath := range appConfig.Scripts {
				fullPath := a.resolveScriptPath(scriptPath)
				if err := a.validateScript(fullPath); err != nil {
					allScriptsValid = false
					invalidScripts = append(invalidScripts, filepath.Base(scriptPath))
				}
			}

			if allScriptsValid {
				item.Status = "ready"
			} else {
				item.Status = "error"
				item.Error = fmt.Sprintf("Invalid scripts: %s", strings.Join(invalidScripts, ", "))
			}
		}

		status.Items = append(status.Items, item)
	}

	return status, nil
}

// Install runs all scripts for specified apps
func (a *AppsTool) Install(ctx context.Context, items []string) (*types.OperationResult, error) {
	return a.runApps(ctx, items, "install")
}

// Update runs scripts for specified apps (same as install for custom apps)
func (a *AppsTool) Update(ctx context.Context, items []string) (*types.OperationResult, error) {
	return a.runApps(ctx, items, "update")
}

// Remove is not typically used for custom apps
func (a *AppsTool) Remove(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      a.Name(),
		Operation: "remove",
		Success:   true,
		Details:   map[string]interface{}{"message": "remove operation not supported for custom apps"},
	}
	return result, nil
}

// List returns all configured apps
func (a *AppsTool) List(ctx context.Context) ([]types.ToolItem, error) {
	status, err := a.Status(ctx)
	if err != nil {
		return nil, err
	}
	return status.Items, nil
}

// Sync runs all enabled apps
func (a *AppsTool) Sync(ctx context.Context) (*types.OperationResult, error) {
	var enabledApps []string
	for appName, appConfig := range *a.config {
		if appConfig.Enabled {
			enabledApps = append(enabledApps, appName)
		}
	}
	return a.runApps(ctx, enabledApps, "sync")
}

// Configure updates the tool configuration
func (a *AppsTool) Configure(cfg interface{}) error {
	config, ok := cfg.(*config.AppsConfig)
	if !ok {
		return fmt.Errorf("invalid configuration type for apps tool")
	}
	a.config = config
	return nil
}

// Helper methods

func (a *AppsTool) runApps(ctx context.Context, items []string, operation string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      a.Name(),
		Operation: operation,
		Success:   true,
		Details:   make(map[string]interface{}),
	}

	var errors []string
	var executed []string

	// If no specific items provided, run all enabled apps
	apps := items
	if len(apps) == 0 {
		for appName, appConfig := range *a.config {
			if appConfig.Enabled {
				apps = append(apps, appName)
			}
		}
	}

	for _, appName := range apps {
		if err := a.runApp(ctx, appName); err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", appName, err))
			result.Success = false
		} else {
			executed = append(executed, appName)
		}
	}

	result.Details["executed"] = executed
	result.Details["errors"] = errors

	if len(errors) > 0 {
		result.Error = fmt.Errorf("failed to run some apps: %s", strings.Join(errors, "; "))
	}

	return result, nil
}

func (a *AppsTool) runApp(ctx context.Context, appName string) error {
	appConfig, exists := (*a.config)[appName]
	if !exists {
		return fmt.Errorf("app %s not found", appName)
	}

	if !appConfig.Enabled {
		return fmt.Errorf("app %s is disabled", appName)
	}

	// Execute all scripts for this app in order
	for i, scriptPath := range appConfig.Scripts {
		fullPath := a.resolveScriptPath(scriptPath)

		if err := a.validateScript(fullPath); err != nil {
			return fmt.Errorf("script %s is invalid: %w", scriptPath, err)
		}

		if a.dryRun {
			fmt.Printf("[DRY RUN] Would execute script: %s\n", fullPath)
			continue
		}

		if err := a.executeScript(ctx, fullPath); err != nil {
			return fmt.Errorf("script %s failed (step %d): %w", scriptPath, i+1, err)
		}
	}

	return nil
}

func (a *AppsTool) resolveScriptPath(scriptPath string) string {
	if filepath.IsAbs(scriptPath) {
		return scriptPath
	}
	return filepath.Join(a.dotfilesPath, scriptPath)
}

func (a *AppsTool) validateScript(scriptPath string) error {
	// Check if script exists
	info, err := os.Stat(scriptPath)
	if err != nil {
		return fmt.Errorf("script not found: %w", err)
	}

	// Check if script is executable
	if info.Mode()&0111 == 0 {
		return fmt.Errorf("script is not executable")
	}

	return nil
}

func (a *AppsTool) executeScript(ctx context.Context, scriptPath string) error {
	// Determine the interpreter based on configurable file extension mappings
	var cmd *exec.Cmd
	ext := filepath.Ext(scriptPath)

	if interpreter, exists := a.interpreters[ext]; exists {
		cmd = exec.CommandContext(ctx, interpreter, scriptPath)
	} else {
		// Try to execute directly (assuming it has shebang)
		cmd = exec.CommandContext(ctx, scriptPath)
	}

	// Set working directory to dotfiles root, not script directory
	// This ensures scripts can access relative paths correctly
	cmd.Dir = a.dotfilesPath

	// Connect stdout/stderr to current process for proper TTY handling
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// Run the command and wait for completion
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("execution failed: %w", err)
	}

	return nil
}
