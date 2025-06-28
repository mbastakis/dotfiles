package rsync

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/yourusername/dotfiles/internal/config"
	"github.com/yourusername/dotfiles/internal/types"
)

// RsyncTool implements the Tool interface for Rsync file synchronization
type RsyncTool struct {
	config       *config.RsyncConfig
	dotfilesPath string
	backupSuffix string
	dryRun       bool
}

// NewRsyncTool creates a new RsyncTool instance
func NewRsyncTool(cfg *config.Config) *RsyncTool {
	return &RsyncTool{
		config:       &cfg.Rsync,
		dotfilesPath: cfg.Global.DotfilesPath,
		backupSuffix: cfg.Global.BackupSuffix,
		dryRun:       cfg.Global.DryRun,
	}
}

// Name returns the tool name
func (r *RsyncTool) Name() string {
	return "rsync"
}

// IsEnabled returns whether the tool is enabled
func (r *RsyncTool) IsEnabled() bool {
	return r.config.Enabled
}

// Priority returns the tool priority
func (r *RsyncTool) Priority() int {
	return 20 // Higher than stow to run after configuration is linked
}

// Validate checks if rsync is available and sources are valid
func (r *RsyncTool) Validate() error {
	// Check if rsync command is available
	if _, err := exec.LookPath("rsync"); err != nil {
		return fmt.Errorf("rsync command not found: %w", err)
	}

	// Validate source directories exist
	for _, source := range r.config.Sources {
		if !source.Enabled {
			continue
		}

		sourcePath := r.resolveSourcePath(source.Name)
		if _, err := os.Stat(sourcePath); err != nil {
			return fmt.Errorf("source directory %s does not exist: %w", sourcePath, err)
		}
	}

	return nil
}

// Status returns the current status of rsync sources
func (r *RsyncTool) Status(ctx context.Context) (*types.ToolStatus, error) {
	status := &types.ToolStatus{
		Name:      r.Name(),
		Enabled:   r.IsEnabled(),
		Healthy:   true,
		LastCheck: time.Now(),
		Items:     make([]types.ToolItem, 0),
	}

	if !r.IsEnabled() {
		return status, nil
	}

	for _, source := range r.config.Sources {
		item := types.ToolItem{
			Name:        source.Name,
			Description: fmt.Sprintf("Sync to %s", source.Target),
			Status:      "unknown",
			Enabled:     source.Enabled,
			Priority:    source.Priority,
		}

		if !source.Enabled {
			item.Status = "disabled"
		} else {
			// Check if source exists and target is synced
			sourcePath := r.resolveSourcePath(source.Name)
			targetPath := r.resolveTargetPath(source.Target)

			if _, err := os.Stat(sourcePath); err != nil {
				item.Status = "error"
				item.Error = fmt.Sprintf("Source not found: %s", sourcePath)
			} else if r.needsSync(sourcePath, targetPath) {
				item.Status = "needs_sync"
			} else {
				item.Status = "synced"
			}
		}

		status.Items = append(status.Items, item)
	}

	return status, nil
}

// Install syncs specific sources to their targets
func (r *RsyncTool) Install(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      r.Name(),
		Operation: "sync",
		Success:   true,
		Details:   make(map[string]interface{}),
	}

	var errors []string
	var synced []string

	// If no specific items provided, sync all enabled sources
	if len(items) == 0 {
		for _, source := range r.config.Sources {
			if source.Enabled {
				items = append(items, source.Name)
			}
		}
	}

	for _, sourceName := range items {
		if err := r.syncSource(sourceName); err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", sourceName, err))
			result.Success = false
		} else {
			synced = append(synced, sourceName)
		}
	}

	result.Details["synced"] = synced
	result.Details["errors"] = errors

	if len(errors) > 0 {
		result.Error = fmt.Errorf("failed to sync some sources: %s", strings.Join(errors, "; "))
	}

	return result, nil
}

// Update is an alias for Install for rsync
func (r *RsyncTool) Update(ctx context.Context, items []string) (*types.OperationResult, error) {
	result, err := r.Install(ctx, items)
	if result != nil {
		result.Operation = "update"
	}
	return result, err
}

// Remove deletes synced content (with backup if enabled)
func (r *RsyncTool) Remove(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Tool:      r.Name(),
		Operation: "remove",
		Success:   true,
		Details:   make(map[string]interface{}),
	}

	var errors []string
	var removed []string

	for _, sourceName := range items {
		source := r.findSource(sourceName)
		if source == nil {
			errors = append(errors, fmt.Sprintf("source %s not found", sourceName))
			continue
		}

		targetPath := r.resolveTargetPath(source.Target)
		if _, err := os.Stat(targetPath); os.IsNotExist(err) {
			continue // Already removed
		}

		// Create backup if enabled
		if r.backupSuffix != "" {
			backupPath := targetPath + r.backupSuffix
			if err := os.Rename(targetPath, backupPath); err != nil {
				errors = append(errors, fmt.Sprintf("failed to backup %s: %v", targetPath, err))
				result.Success = false
				continue
			}
		} else {
			// Remove without backup
			if err := os.RemoveAll(targetPath); err != nil {
				errors = append(errors, fmt.Sprintf("failed to remove %s: %v", targetPath, err))
				result.Success = false
				continue
			}
		}

		removed = append(removed, sourceName)
	}

	result.Details["removed"] = removed
	result.Details["errors"] = errors

	if len(errors) > 0 {
		result.Error = fmt.Errorf("failed to remove some sources: %s", strings.Join(errors, "; "))
	}

	return result, nil
}

// List returns all configured rsync sources
func (r *RsyncTool) List(ctx context.Context) ([]types.ToolItem, error) {
	status, err := r.Status(ctx)
	if err != nil {
		return nil, err
	}
	return status.Items, nil
}

// Sync synchronizes all enabled sources
func (r *RsyncTool) Sync(ctx context.Context) (*types.OperationResult, error) {
	return r.Install(ctx, nil)
}

// Configure updates the tool configuration
func (r *RsyncTool) Configure(cfg interface{}) error {
	config, ok := cfg.(*config.RsyncConfig)
	if !ok {
		return fmt.Errorf("invalid configuration type for rsync tool")
	}
	r.config = config
	return nil
}

// Helper methods

func (r *RsyncTool) resolveSourcePath(sourceName string) string {
	return filepath.Join(r.dotfilesPath, sourceName)
}

func (r *RsyncTool) resolveTargetPath(target string) string {
	// Expand environment variables and home directory
	if strings.HasPrefix(target, "~/") {
		home, _ := os.UserHomeDir()
		target = filepath.Join(home, target[2:])
	}
	target = os.ExpandEnv(target)
	return target
}

func (r *RsyncTool) findSource(name string) *config.RsyncSource {
	for _, source := range r.config.Sources {
		if source.Name == name {
			return &source
		}
	}
	return nil
}

func (r *RsyncTool) needsSync(sourcePath, targetPath string) bool {
	// Simple check: if target doesn't exist, needs sync
	if _, err := os.Stat(targetPath); os.IsNotExist(err) {
		return true
	}

	// For now, assume needs sync if source is newer
	// In a more sophisticated implementation, we'd compare directory contents
	sourceInfo, err := os.Stat(sourcePath)
	if err != nil {
		return false
	}

	targetInfo, err := os.Stat(targetPath)
	if err != nil {
		return true
	}

	return sourceInfo.ModTime().After(targetInfo.ModTime())
}

func (r *RsyncTool) syncSource(sourceName string) error {
	source := r.findSource(sourceName)
	if source == nil {
		return fmt.Errorf("source %s not found", sourceName)
	}

	if !source.Enabled {
		return fmt.Errorf("source %s is disabled", sourceName)
	}

	sourcePath := r.resolveSourcePath(source.Name)
	targetPath := r.resolveTargetPath(source.Target)

	// Ensure target directory exists
	if err := os.MkdirAll(filepath.Dir(targetPath), 0755); err != nil {
		return fmt.Errorf("failed to create target directory: %w", err)
	}

	// Build rsync command
	args := []string{
		"-av", // Archive mode, verbose
		"--delete", // Delete files not in source
	}

	if r.dryRun {
		args = append(args, "--dry-run")
	}

	// Add trailing slash to ensure directory contents are synced
	if !strings.HasSuffix(sourcePath, "/") {
		sourcePath += "/"
	}

	args = append(args, sourcePath, targetPath)

	// Execute rsync
	cmd := exec.Command("rsync", args...)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("rsync failed: %w\nOutput: %s", err, string(output))
	}

	return nil
}