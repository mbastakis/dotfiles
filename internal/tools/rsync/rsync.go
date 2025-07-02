package rsync

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/types"
)

// RsyncTool implements the Tool interface for Rsync file synchronization
type RsyncTool struct {
	config       *config.RsyncConfig
	dotfilesPath string
	dryRun       bool
	statusCache  map[string]*statusCacheEntry
	cacheMutex   sync.RWMutex
}

type statusCacheEntry struct {
	status    string
	timestamp time.Time
	ttl       time.Duration
}

// NewRsyncTool creates a new RsyncTool instance
func NewRsyncTool(cfg *config.Config) *RsyncTool {
	return &RsyncTool{
		config:       &cfg.Rsync,
		dotfilesPath: cfg.Global.DotfilesPath,
		dryRun:       cfg.Global.DryRun,
		statusCache:  make(map[string]*statusCacheEntry),
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
			} else if r.needsSyncCached(sourcePath, targetPath) {
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

	// Process sources in parallel for better performance
	type syncResult struct {
		sourceName string
		err        error
	}

	resultChan := make(chan syncResult, len(items))
	semaphore := make(chan struct{}, 3) // Limit concurrent syncs to 3

	for _, sourceName := range items {
		go func(name string) {
			semaphore <- struct{}{}        // Acquire
			defer func() { <-semaphore }() // Release

			err := r.syncSource(name)
			resultChan <- syncResult{sourceName: name, err: err}
		}(sourceName)
	}

	// Collect results
	for i := 0; i < len(items); i++ {
		syncRes := <-resultChan
		if syncRes.err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", syncRes.sourceName, syncRes.err))
			result.Success = false
		} else {
			synced = append(synced, syncRes.sourceName)
			// Clear cache entry for this source
			r.clearStatusCache(syncRes.sourceName)
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

// Remove deletes synced content
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

		// Remove target directory
		if err := os.RemoveAll(targetPath); err != nil {
			errors = append(errors, fmt.Sprintf("failed to remove %s: %v", targetPath, err))
			result.Success = false
			continue
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
	// Use the same verification logic as sync verification
	// This ensures consistency between sync and status checks
	return !r.verifySync(sourcePath+"/", targetPath)
}

// needsSyncCached checks if sync is needed using cached results
func (r *RsyncTool) needsSyncCached(sourcePath, targetPath string) bool {
	cacheKey := sourcePath + "->" + targetPath

	r.cacheMutex.RLock()
	entry, exists := r.statusCache[cacheKey]
	r.cacheMutex.RUnlock()

	// Check if cache entry is valid
	if exists && time.Since(entry.timestamp) < entry.ttl {
		return entry.status == "needs_sync"
	}

	// Cache miss or expired, compute and cache result
	needsSync := r.needsSync(sourcePath, targetPath)
	status := "synced"
	if needsSync {
		status = "needs_sync"
	}

	r.cacheMutex.Lock()
	r.statusCache[cacheKey] = &statusCacheEntry{
		status:    status,
		timestamp: time.Now(),
		ttl:       30 * time.Second, // Cache for 30 seconds
	}
	r.cacheMutex.Unlock()

	return needsSync
}

// clearStatusCache clears cache entry for a source
func (r *RsyncTool) clearStatusCache(sourceName string) {
	r.cacheMutex.Lock()
	defer r.cacheMutex.Unlock()

	for key := range r.statusCache {
		if strings.HasPrefix(key, r.resolveSourcePath(sourceName)) {
			delete(r.statusCache, key)
		}
	}
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

	// Build optimized rsync command
	args := []string{
		"-rlptD",          // Recursive, links, perms, times, devices (like -a but no verbose/group)
		"--compress",      // Compress during transfer for better performance
		"--whole-file",    // Don't use delta-xfer algorithm for small files
		"--ignore-errors", // Continue despite errors
		"--partial",       // Keep partially transferred files
	}

	// Only use --delete if target is not a system directory
	if !r.isSystemDirectory(targetPath) {
		args = append(args, "--delete")
	}

	if r.dryRun {
		args = append(args, "--dry-run")
	}

	// Add trailing slash to ensure directory contents are synced
	if !strings.HasSuffix(sourcePath, "/") {
		sourcePath += "/"
	}

	args = append(args, sourcePath, targetPath)

	// Execute rsync with timeout context
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, "rsync", args...)
	output, err := cmd.CombinedOutput()

	if err != nil {
		// Check if this is an acceptable rsync exit code
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode := exitErr.ExitCode()

			// Handle specific rsync exit codes
			switch exitCode {
			case 23:
				// Partial transfer due to error (often permission warnings on macOS)
				// Check if the intended files were actually synced successfully
				if r.verifySync(sourcePath, targetPath) {
					// Files were synced successfully despite warnings
					return nil
				}
				// If verification failed, treat as real error
				return fmt.Errorf("rsync partial failure - intended files not synced: %w\nOutput: %s", err, string(output))
			case 24:
				// Partial transfer due to vanished source files (usually acceptable)
				if r.verifySync(sourcePath, targetPath) {
					return nil
				}
				return fmt.Errorf("rsync failed - source files vanished: %w\nOutput: %s", err, string(output))
			default:
				// Other exit codes are treated as errors
				return fmt.Errorf("rsync failed: %w\nOutput: %s", err, string(output))
			}
		}
		// Non-exit errors (e.g., command not found) are always errors
		return fmt.Errorf("rsync failed: %w\nOutput: %s", err, string(output))
	}

	return nil
}

// verifySync checks if the source files were successfully synced to the target
func (r *RsyncTool) verifySync(sourcePath, targetPath string) bool {
	// Remove trailing slash for consistent comparison
	sourcePath = strings.TrimSuffix(sourcePath, "/")

	// Walk through source directory and verify each file exists in target
	return filepath.Walk(sourcePath, func(srcFile string, srcInfo os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Calculate relative path from source
		relPath, err := filepath.Rel(sourcePath, srcFile)
		if err != nil {
			return err
		}

		// Skip if this is the source directory itself
		if relPath == "." {
			return nil
		}

		// Calculate corresponding target path
		targetFile := filepath.Join(targetPath, relPath)

		// Check if target file/dir exists
		targetInfo, err := os.Stat(targetFile)
		if err != nil {
			// Target file doesn't exist - sync failed
			return fmt.Errorf("target file missing: %s", targetFile)
		}

		// For files, verify size and modification time are reasonable
		if srcInfo.Mode().IsRegular() && targetInfo.Mode().IsRegular() {
			if srcInfo.Size() != targetInfo.Size() {
				return fmt.Errorf("file size mismatch: %s", targetFile)
			}
		}

		return nil
	}) == nil
}

// isSystemDirectory checks if the target path is a system directory where --delete should not be used
func (r *RsyncTool) isSystemDirectory(targetPath string) bool {
	// Get user home directory
	home, err := os.UserHomeDir()
	if err != nil {
		return false
	}

	// Normalize paths for comparison
	targetPath = filepath.Clean(targetPath)
	home = filepath.Clean(home)

	// If target is exactly the home directory, it's a system directory
	if targetPath == home {
		return true
	}

	// Check for other system directories
	systemDirs := []string{
		"/System",
		"/Library",
		"/usr",
		"/bin",
		"/sbin",
		"/Applications",
		home + "/Library",
		home + "/Applications",
	}

	for _, sysDir := range systemDirs {
		if strings.HasPrefix(targetPath, filepath.Clean(sysDir)) {
			return true
		}
	}

	return false
}
