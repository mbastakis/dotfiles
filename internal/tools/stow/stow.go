package stow

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/yourusername/dotfiles/internal/config"
	"github.com/yourusername/dotfiles/internal/tools"
	"github.com/yourusername/dotfiles/internal/types"
)

// StowTool implements the Tool interface for GNU Stow operations
type StowTool struct {
	config       *config.StowConfig
	dotfilesPath string
	backupSuffix string
	enabled      bool
	dryRun       bool
}

// NewStowTool creates a new StowTool instance
func NewStowTool(cfg *config.Config) *StowTool {
	return &StowTool{
		config:       &cfg.Stow,
		dotfilesPath: cfg.Global.DotfilesPath,
		backupSuffix: cfg.Global.BackupSuffix,
		enabled:      true,
		dryRun:       cfg.Global.DryRun,
	}
}

// Name returns the tool name
func (s *StowTool) Name() string {
	return "stow"
}

// IsEnabled returns whether the tool is enabled
func (s *StowTool) IsEnabled() bool {
	return s.enabled
}

// Priority returns the tool priority (stow should run early)
func (s *StowTool) Priority() int {
	return 1
}

// Validate checks if the tool is properly configured and dependencies are available
func (s *StowTool) Validate() error {
	// Check if stow command is available
	if _, err := exec.LookPath("stow"); err != nil {
		return tools.ErrStowNotFound
	}

	// Check if dotfiles path exists
	if _, err := os.Stat(s.dotfilesPath); os.IsNotExist(err) {
		return fmt.Errorf("dotfiles path does not exist: %s", s.dotfilesPath)
	}

	// Validate package configurations
	for _, pkg := range s.config.Packages {
		if err := s.validatePackage(pkg); err != nil {
			return fmt.Errorf("invalid package %s: %w", pkg.Name, err)
		}
	}

	return nil
}

// Status returns the current status of stow packages
func (s *StowTool) Status(ctx context.Context) (*types.ToolStatus, error) {
	status := &types.ToolStatus{
		Name:      s.Name(),
		Enabled:   s.enabled,
		Healthy:   true,
		LastCheck: time.Now(),
		Items:     make([]types.ToolItem, 0, len(s.config.Packages)),
	}

	for _, pkg := range s.config.Packages {
		item := types.ToolItem{
			Name:     pkg.Name,
			Enabled:  pkg.Enabled,
			Target:   pkg.Target,
			Priority: pkg.Priority,
		}

		// Check if package is linked
		linked, err := s.isPackageLinked(pkg)
		if err != nil {
			status.Healthy = false
			status.Error = err
		}
		item.Installed = linked

		status.Items = append(status.Items, item)
	}

	return status, nil
}

// Install links the specified packages using stow
func (s *StowTool) Install(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Success: true,
		Message: "Packages linked successfully",
	}

	for _, item := range items {
		pkg := s.findPackage(item)
		if pkg == nil {
			result.Success = false
			result.Error = fmt.Errorf("package not found: %s", item)
			return result, result.Error
		}

		if err := s.linkPackage(*pkg); err != nil {
			result.Success = false
			result.Error = err
			result.Message = fmt.Sprintf("Failed to link package %s: %v", item, err)
			return result, err
		}

		result.Modified = append(result.Modified, item)
	}

	return result, nil
}

// Update re-links packages (stow doesn't have traditional updates)
func (s *StowTool) Update(ctx context.Context, items []string) (*types.OperationResult, error) {
	// For stow, update means unlink and relink
	if unlinkResult, err := s.Remove(ctx, items); err != nil {
		return unlinkResult, err
	}

	return s.Install(ctx, items)
}

// Remove unlinks the specified packages
func (s *StowTool) Remove(ctx context.Context, items []string) (*types.OperationResult, error) {
	result := &types.OperationResult{
		Success: true,
		Message: "Packages unlinked successfully",
	}

	for _, item := range items {
		pkg := s.findPackage(item)
		if pkg == nil {
			result.Success = false
			result.Error = fmt.Errorf("package not found: %s", item)
			return result, result.Error
		}

		if err := s.unlinkPackage(*pkg); err != nil {
			result.Success = false
			result.Error = err
			result.Message = fmt.Sprintf("Failed to unlink package %s: %v", item, err)
			return result, err
		}

		result.Modified = append(result.Modified, item)
	}

	return result, nil
}

// List returns all available packages
func (s *StowTool) List(ctx context.Context) ([]types.ToolItem, error) {
	items := make([]types.ToolItem, 0, len(s.config.Packages))

	for _, pkg := range s.config.Packages {
		linked, _ := s.isPackageLinked(pkg)
		
		item := types.ToolItem{
			Name:      pkg.Name,
			Enabled:   pkg.Enabled,
			Installed: linked,
			Target:    pkg.Target,
			Priority:  pkg.Priority,
		}
		
		items = append(items, item)
	}

	return items, nil
}

// Sync links all enabled packages
func (s *StowTool) Sync(ctx context.Context) (*types.OperationResult, error) {
	var enabledPackages []string
	for _, pkg := range s.config.Packages {
		if pkg.Enabled {
			enabledPackages = append(enabledPackages, pkg.Name)
		}
	}

	return s.Install(ctx, enabledPackages)
}

// Configure updates the tool configuration
func (s *StowTool) Configure(cfg interface{}) error {
	stowCfg, ok := cfg.(*config.StowConfig)
	if !ok {
		return tools.ErrInvalidConfig
	}

	s.config = stowCfg
	return nil
}

// linkPackage links a single package using stow
func (s *StowTool) linkPackage(pkg config.StowPackage) error {
	// Resolve target path with environment variables
	target := s.resolveTarget(pkg.Target)
	
	// Validate target directory exists or can be created
	if err := s.ensureTargetDir(target); err != nil {
		return err
	}

	// Check for conflicts and create backups if needed
	if err := s.handleConflicts(pkg, target); err != nil {
		return err
	}

	// Build stow command
	args := []string{
		"--target=" + target,
		pkg.Name,
	}

	if s.dryRun {
		args = append([]string{"--simulate"}, args...)
	}

	// Execute stow command from config directory
	cmd := exec.Command("stow", args...)
	cmd.Dir = filepath.Join(s.dotfilesPath, "config")
	
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("stow failed: %w\nOutput: %s", err, string(output))
	}

	return nil
}

// unlinkPackage unlinks a single package using stow
func (s *StowTool) unlinkPackage(pkg config.StowPackage) error {
	target := s.resolveTarget(pkg.Target)

	args := []string{
		"--delete",
		"--target=" + target,
		pkg.Name,
	}

	if s.dryRun {
		args = append([]string{"--simulate"}, args...)
	}

	cmd := exec.Command("stow", args...)
	cmd.Dir = filepath.Join(s.dotfilesPath, "config")
	
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("stow delete failed: %w\nOutput: %s", err, string(output))
	}

	// Restore backups if they exist
	if !s.dryRun {
		s.restoreBackups(pkg, target)
	}

	return nil
}

// isPackageLinked checks if a package is currently linked
func (s *StowTool) isPackageLinked(pkg config.StowPackage) (bool, error) {
	target := s.resolveTarget(pkg.Target)
	packagePath := filepath.Join(s.dotfilesPath, "config", pkg.Name)

	// Check if package directory exists
	if _, err := os.Stat(packagePath); os.IsNotExist(err) {
		return false, tools.ErrPackageNotFound
	}

	// Walk through package directory and check if files are linked
	linked := true
	err := filepath.Walk(packagePath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip the package root directory
		if path == packagePath {
			return nil
		}

		// Calculate relative path from package root
		relPath, err := filepath.Rel(packagePath, path)
		if err != nil {
			return err
		}

		// Calculate target path
		targetPath := filepath.Join(target, relPath)

		// Check if target is a symlink pointing to the package file
		if linkTarget, err := os.Readlink(targetPath); err != nil || linkTarget != path {
			linked = false
			return filepath.SkipDir // Stop walking, we know it's not fully linked
		}

		return nil
	})

	return linked && err == nil, err
}

// validatePackage validates a package configuration
func (s *StowTool) validatePackage(pkg config.StowPackage) error {
	if pkg.Name == "" {
		return fmt.Errorf("package name cannot be empty")
	}

	if pkg.Target == "" {
		return fmt.Errorf("package target cannot be empty")
	}

	// Check if package directory exists
	packagePath := filepath.Join(s.dotfilesPath, "config", pkg.Name)
	if _, err := os.Stat(packagePath); os.IsNotExist(err) {
		return tools.ErrPackageNotFound
	}

	return nil
}

// findPackage finds a package by name
func (s *StowTool) findPackage(name string) *config.StowPackage {
	for _, pkg := range s.config.Packages {
		if pkg.Name == name {
			return &pkg
		}
	}
	return nil
}

// resolveTarget resolves environment variables in target path
func (s *StowTool) resolveTarget(target string) string {
	// Expand environment variables
	expanded := os.ExpandEnv(target)
	
	// Expand tilde to home directory
	if strings.HasPrefix(expanded, "~/") {
		if homeDir, err := os.UserHomeDir(); err == nil {
			expanded = filepath.Join(homeDir, expanded[2:])
		}
	}

	return expanded
}

// ensureTargetDir ensures the target directory exists
func (s *StowTool) ensureTargetDir(target string) error {
	if _, err := os.Stat(target); os.IsNotExist(err) {
		if s.dryRun {
			fmt.Printf("Would create directory: %s\n", target)
			return nil
		}
		
		if err := os.MkdirAll(target, 0755); err != nil {
			return fmt.Errorf("failed to create target directory %s: %w", target, err)
		}
	}
	return nil
}

// handleConflicts checks for conflicts and creates backups
func (s *StowTool) handleConflicts(pkg config.StowPackage, target string) error {
	if s.backupSuffix == "" {
		return nil // Backups disabled
	}

	packagePath := filepath.Join(s.dotfilesPath, "config", pkg.Name)
	
	return filepath.Walk(packagePath, func(path string, info os.FileInfo, err error) error {
		if err != nil || path == packagePath {
			return err
		}

		relPath, err := filepath.Rel(packagePath, path)
		if err != nil {
			return err
		}

		targetPath := filepath.Join(target, relPath)
		
		// Check if target exists and is not already a symlink to our package
		if _, err := os.Lstat(targetPath); err == nil {
			if linkTarget, err := os.Readlink(targetPath); err != nil || linkTarget != path {
				// File exists and is not our symlink - create backup
				backupPath := targetPath + s.backupSuffix
				
				if s.dryRun {
					fmt.Printf("Would backup %s to %s\n", targetPath, backupPath)
				} else {
					if err := os.Rename(targetPath, backupPath); err != nil {
						return fmt.Errorf("failed to backup %s: %w", targetPath, err)
					}
				}
			}
		}

		return nil
	})
}

// restoreBackups restores backup files when unlinking
func (s *StowTool) restoreBackups(pkg config.StowPackage, target string) {
	if s.backupSuffix == "" {
		return
	}

	packagePath := filepath.Join(s.dotfilesPath, "config", pkg.Name)
	
	filepath.Walk(packagePath, func(path string, info os.FileInfo, err error) error {
		if err != nil || path == packagePath {
			return err
		}

		relPath, _ := filepath.Rel(packagePath, path)
		targetPath := filepath.Join(target, relPath)
		backupPath := targetPath + s.backupSuffix

		// If backup exists, restore it
		if _, err := os.Stat(backupPath); err == nil {
			os.Rename(backupPath, targetPath)
		}

		return nil
	})
}