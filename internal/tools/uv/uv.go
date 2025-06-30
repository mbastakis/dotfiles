package uv

import (
	"context"
	"encoding/json"
	"fmt"
	"os/exec"
	"strings"
	"time"

	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/types"
)

// UVTool implements the Tool interface for UV Python tool management
type UVTool struct {
	config *config.UVConfig
	dryRun bool
}

// UVToolInfo represents information about a UV tool
type UVToolInfo struct {
	Name    string `json:"name"`
	Version string `json:"version"`
	Path    string `json:"path"`
}

// NewUVTool creates a new UVTool instance
func NewUVTool(cfg *config.Config) *UVTool {
	return &UVTool{
		config: &cfg.UV,
		dryRun: cfg.Global.DryRun,
	}
}

// Name returns the tool name
func (u *UVTool) Name() string {
	return "uv"
}

// IsEnabled returns whether the tool is enabled
func (u *UVTool) IsEnabled() bool {
	return u.config != nil
}

// Priority returns the tool priority
func (u *UVTool) Priority() int {
	return 60 // Run last after all other tools
}

// Validate checks if uv is available and tools are valid
func (u *UVTool) Validate() error {
	// Check if uv command is available
	if _, err := exec.LookPath("uv"); err != nil {
		return fmt.Errorf("uv command not found: %w", err)
	}

	// Check if Python is available (uv requires Python)
	if _, err := exec.LookPath("python3"); err != nil {
		if _, err := exec.LookPath("python"); err != nil {
			return fmt.Errorf("python command not found: %w", err)
		}
	}

	return nil
}

// Status returns the current status of UV tools
func (u *UVTool) Status(ctx context.Context) (*types.ToolStatus, error) {
	status := &types.ToolStatus{
		Name:      u.Name(),
		Enabled:   u.IsEnabled(),
		Healthy:   true,
		LastCheck: time.Now(),
		Items:     make([]types.ToolItem, 0),
	}

	if !u.IsEnabled() {
		return status, nil
	}

	installedTools, err := u.getInstalledTools()
	if err != nil {
		status.Healthy = false
		status.Error = err
		return status, nil
	}

	for _, toolName := range u.config.GlobalPackages {
		item := types.ToolItem{
			Name:        toolName,
			Description: "UV Python tool",
			Enabled:     true,
		}

		if installedTool, exists := installedTools[toolName]; exists {
			item.Status = "installed"
			item.Version = installedTool.Version
			item.Description = fmt.Sprintf("UV Python tool (v%s)", installedTool.Version)
		} else {
			item.Status = "not_installed"
		}

		status.Items = append(status.Items, item)
	}

	return status, nil
}

// Install installs specified UV tools
func (u *UVTool) Install(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      u.Name(),
		Operation: "install",
		Success:   true,
		Details:   make(map[string]interface{}),
	}

	var errors []string
	var installed []string

	// If no specific items provided, install all configured tools
	tools := items
	if len(tools) == 0 {
		tools = u.config.GlobalPackages
	}

	for _, toolName := range tools {
		if err := u.installTool(toolName); err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", toolName, err))
			result.Success = false
		} else {
			installed = append(installed, toolName)
		}
	}

	result.Details["installed"] = installed
	result.Details["errors"] = errors

	if len(errors) > 0 {
		result.Error = fmt.Errorf("failed to install some tools: %s", strings.Join(errors, "; "))
	}

	return result, nil
}

// Update updates specified UV tools or all if none specified
func (u *UVTool) Update(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      u.Name(),
		Operation: "update",
		Success:   true,
		Details:   make(map[string]interface{}),
	}

	var errors []string
	var updated []string

	tools := items
	if len(tools) == 0 {
		tools = u.config.GlobalPackages
	}

	for _, toolName := range tools {
		if err := u.updateTool(toolName); err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", toolName, err))
			result.Success = false
		} else {
			updated = append(updated, toolName)
		}
	}

	result.Details["updated"] = updated
	result.Details["errors"] = errors

	if len(errors) > 0 {
		result.Error = fmt.Errorf("failed to update some tools: %s", strings.Join(errors, "; "))
	}

	return result, nil
}

// Remove removes specified UV tools
func (u *UVTool) Remove(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      u.Name(),
		Operation: "remove",
		Success:   true,
		Details:   make(map[string]interface{}),
	}

	var errors []string
	var removed []string

	for _, toolName := range items {
		if err := u.removeTool(toolName); err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", toolName, err))
			result.Success = false
		} else {
			removed = append(removed, toolName)
		}
	}

	result.Details["removed"] = removed
	result.Details["errors"] = errors

	if len(errors) > 0 {
		result.Error = fmt.Errorf("failed to remove some tools: %s", strings.Join(errors, "; "))
	}

	return result, nil
}

// List returns all configured UV tools
func (u *UVTool) List(ctx context.Context) ([]types.ToolItem, error) {
	status, err := u.Status(ctx)
	if err != nil {
		return nil, err
	}
	return status.Items, nil
}

// Sync installs all configured tools if auto_install is enabled
func (u *UVTool) Sync(ctx context.Context) (*types.OperationResult, error) {
	if u.config.AutoInstall {
		return u.Install(ctx, nil)
	}

	// If auto_install is disabled, just return success without doing anything
	return &types.OperationResult{
		Tool:      u.Name(),
		Operation: "sync",
		Success:   true,
		Details:   map[string]interface{}{"message": "auto_install disabled"},
	}, nil
}

// Configure updates the tool configuration
func (u *UVTool) Configure(cfg interface{}) error {
	config, ok := cfg.(*config.UVConfig)
	if !ok {
		return fmt.Errorf("invalid configuration type for uv tool")
	}
	u.config = config
	return nil
}

// Helper methods

func (u *UVTool) installTool(toolName string) error {
	args := []string{"tool", "install", toolName}
	if u.dryRun {
		// UV doesn't have a built-in dry-run for tool install, so we'll simulate it
		return nil
	}

	cmd := exec.Command("uv", args...)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("uv tool install failed: %w\nOutput: %s", err, string(output))
	}

	return nil
}

func (u *UVTool) updateTool(toolName string) error {
	args := []string{"tool", "upgrade", toolName}
	if u.dryRun {
		return nil
	}

	cmd := exec.Command("uv", args...)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("uv tool upgrade failed: %w\nOutput: %s", err, string(output))
	}

	return nil
}

func (u *UVTool) removeTool(toolName string) error {
	args := []string{"tool", "uninstall", toolName}
	if u.dryRun {
		return nil
	}

	cmd := exec.Command("uv", args...)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("uv tool uninstall failed: %w\nOutput: %s", err, string(output))
	}

	return nil
}

func (u *UVTool) getInstalledTools() (map[string]UVToolInfo, error) {
	cmd := exec.Command("uv", "tool", "list", "--format", "json")
	output, err := cmd.Output()
	if err != nil {
		// If JSON format is not supported, fall back to regular list
		return u.getInstalledToolsFallback()
	}

	var tools []UVToolInfo
	if err := json.Unmarshal(output, &tools); err != nil {
		// JSON parsing failed, fall back to text parsing
		return u.getInstalledToolsFallback()
	}

	toolMap := make(map[string]UVToolInfo)
	for _, tool := range tools {
		toolMap[tool.Name] = tool
	}

	return toolMap, nil
}

func (u *UVTool) getInstalledToolsFallback() (map[string]UVToolInfo, error) {
	cmd := exec.Command("uv", "tool", "list")
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to list uv tools: %w", err)
	}

	tools := make(map[string]UVToolInfo)
	lines := strings.Split(string(output), "\n")

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// Parse tool list output (format may vary, this is a simple parser)
		// Expected format: "tool-name v1.0.0 (/path/to/tool)"
		parts := strings.Fields(line)
		if len(parts) >= 2 {
			name := parts[0]
			version := strings.TrimPrefix(parts[1], "v")
			
			tools[name] = UVToolInfo{
				Name:    name,
				Version: version,
			}
		}
	}

	return tools, nil
}