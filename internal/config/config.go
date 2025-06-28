package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"
)

// Config represents the main configuration structure
type Config struct {
	Global   GlobalConfig   `yaml:"global"`
	TUI      TUIConfig      `yaml:"tui"`
	Stow     StowConfig     `yaml:"stow"`
	Rsync    RsyncConfig    `yaml:"rsync"`
	Homebrew HomebrewConfig `yaml:"homebrew"`
	NPM      NPMConfig      `yaml:"npm"`
	UV       UVConfig       `yaml:"uv"`
	Apps     AppsConfig     `yaml:"apps"`
}

// GlobalConfig represents global application settings
type GlobalConfig struct {
	DotfilesPath   string `yaml:"dotfiles_path"`
	LogLevel       string `yaml:"log_level"`
	DryRun         bool   `yaml:"dry_run"`
	AutoConfirm    bool   `yaml:"auto_confirm"`
	BackupEnabled  bool   `yaml:"backup_enabled"`
	BackupSuffix   string `yaml:"backup_suffix"`
}

// TUIConfig represents TUI-specific settings
type TUIConfig struct {
	ColorScheme          string `yaml:"color_scheme"`
	Animations           bool   `yaml:"animations"`
	ConfirmDestructive   bool   `yaml:"confirm_destructive"`
	ShowProgress         bool   `yaml:"show_progress"`
}

// StowConfig represents GNU Stow configuration
type StowConfig struct {
	Packages []StowPackage `yaml:"packages"`
}

// StowPackage represents a single stow package configuration
type StowPackage struct {
	Name     string `yaml:"name"`
	Target   string `yaml:"target"`
	Enabled  bool   `yaml:"enabled"`
	Priority int    `yaml:"priority"`
}

// RsyncConfig represents rsync operation configuration
type RsyncConfig struct {
	Enabled bool          `yaml:"enabled"`
	Sources []RsyncSource `yaml:"sources"`
}

// RsyncSource represents a single rsync source configuration
type RsyncSource struct {
	Name     string `yaml:"name"`
	Target   string `yaml:"target"`
	Enabled  bool   `yaml:"enabled"`
	Priority int    `yaml:"priority"`
}

// HomebrewConfig represents Homebrew package management configuration
type HomebrewConfig struct {
	AutoUpdate bool                          `yaml:"auto_update"`
	Categories map[string]HomebrewCategory   `yaml:"categories"`
}

// HomebrewCategory represents a Homebrew package category
type HomebrewCategory struct {
	Enabled   bool   `yaml:"enabled"`
	Brewfile  string `yaml:"brewfile"`
}

// NPMConfig represents NPM global package configuration
type NPMConfig struct {
	AutoInstall     bool     `yaml:"auto_install"`
	AutoUpdate      bool     `yaml:"auto_update"`
	GlobalPackages  []string `yaml:"global_packages"`
}

// UVConfig represents UV tool package configuration
type UVConfig struct {
	AutoInstall     bool     `yaml:"auto_install"`
	AutoUpdate      bool     `yaml:"auto_update"`
	GlobalPackages  []string `yaml:"global_packages"`
}

// AppsConfig represents custom application configuration
type AppsConfig map[string]AppConfig

// AppConfig represents a single custom application configuration
type AppConfig struct {
	Enabled bool     `yaml:"enabled"`
	Scripts []string `yaml:"scripts"`
}

// DefaultConfig returns a configuration with sensible defaults
func DefaultConfig() *Config {
	homeDir, _ := os.UserHomeDir()
	
	return &Config{
		Global: GlobalConfig{
			DotfilesPath:  filepath.Join(homeDir, "dev", "dotfiles"),
			LogLevel:      "info",
			DryRun:        false,
			AutoConfirm:   false,
			BackupEnabled: true,
			BackupSuffix:  ".backup",
		},
		TUI: TUIConfig{
			ColorScheme:        "default",
			Animations:         true,
			ConfirmDestructive: true,
			ShowProgress:       true,
		},
		Stow: StowConfig{
			Packages: []StowPackage{
				{Name: "config", Target: "~/.config", Enabled: true, Priority: 1},
				{Name: "shell", Target: "~/", Enabled: true, Priority: 2},
				{Name: "git", Target: "~/", Enabled: true, Priority: 3},
			},
		},
		Rsync: RsyncConfig{
			Enabled: true,
			Sources: []RsyncSource{
				{Name: "claude", Target: "~/", Enabled: true, Priority: 1},
			},
		},
		Homebrew: HomebrewConfig{
			AutoUpdate: true,
			Categories: map[string]HomebrewCategory{
				"core": {Enabled: true, Brewfile: "homebrew/Brewfile"},
				"apps": {Enabled: false, Brewfile: "homebrew/Brewfile.apps"},
				"dev":  {Enabled: false, Brewfile: "homebrew/Brewfile.dev"},
				"mas":  {Enabled: false, Brewfile: "homebrew/Brewfile.mas"},
			},
		},
		NPM: NPMConfig{
			AutoInstall:    true,
			AutoUpdate:     true,
			GlobalPackages: []string{"@anthropic-ai/claude-code"},
		},
		UV: UVConfig{
			AutoInstall:    true,
			AutoUpdate:     true,
			GlobalPackages: []string{"parllama"},
		},
		Apps: AppsConfig{
			"vscode_extensions": {
				Enabled: true,
				Scripts: []string{"data/scripts/build_vscode_extensions.sh"},
			},
		},
	}
}

// LoadWithBootstrap loads configuration with bootstrap-friendly fallback logic
func LoadWithBootstrap(primaryPath string) (*Config, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return nil, fmt.Errorf("failed to get home directory: %w", err)
	}

	// Define the search order for configuration files
	searchPaths := []string{}
	
	// 1. CLI flag path (if provided and not empty)
	if primaryPath != "" {
		expandedPath := primaryPath
		if strings.HasPrefix(primaryPath, "~/") {
			expandedPath = filepath.Join(homeDir, primaryPath[2:])
		}
		searchPaths = append(searchPaths, expandedPath)
	}
	
	// 2. ~/.config/dotfiles/config.yaml (current standard location)
	standardPath := filepath.Join(homeDir, ".config", "dotfiles", "config.yaml")
	searchPaths = append(searchPaths, standardPath)
	
	// 3. Stow-managed location (bootstrap fallback)
	// Find dotfiles directory by looking for go.mod or other indicators
	dotfilesPath := findDotfilesDirectory()
	if dotfilesPath != "" {
		stowPath := filepath.Join(dotfilesPath, "config", "config", ".config", "dotfiles", "config.yaml")
		searchPaths = append(searchPaths, stowPath)
	}

	// Try each path in order
	for _, path := range searchPaths {
		if config, err := loadFromPath(path); err == nil {
			return config, nil
		}
	}

	// Final fallback: return default config
	return DefaultConfig(), nil
}

// Load loads configuration from file (maintains backward compatibility)
func Load(path string) (*Config, error) {
	return LoadWithBootstrap(path)
}

// loadFromPath attempts to load configuration from a specific path
func loadFromPath(path string) (*Config, error) {
	// Check if file exists
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return nil, fmt.Errorf("config file does not exist: %s", path)
	}

	// Read config file
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	// Parse YAML
	var config Config
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse config: %w", err)
	}

	// Validate and set defaults for missing fields
	if err := config.setDefaults(); err != nil {
		return nil, fmt.Errorf("failed to set defaults: %w", err)
	}

	return &config, nil
}

// findDotfilesDirectory attempts to find the dotfiles repository directory
func findDotfilesDirectory() string {
	// Try common locations and look for indicators
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	
	// Common dotfiles locations to check
	candidates := []string{
		filepath.Join(homeDir, "dev", "dotfiles"),
		filepath.Join(homeDir, "dotfiles"),
		filepath.Join(homeDir, ".dotfiles"),
		filepath.Join(homeDir, "Projects", "dotfiles"),
		filepath.Join(homeDir, "Code", "dotfiles"),
	}
	
	// Add current working directory if it looks like dotfiles repo
	if cwd, err := os.Getwd(); err == nil {
		candidates = append([]string{cwd}, candidates...)
	}
	
	// Check each candidate for dotfiles indicators
	for _, candidate := range candidates {
		if isDotfilesDirectory(candidate) {
			return candidate
		}
	}
	
	return ""
}

// isDotfilesDirectory checks if a directory appears to be a dotfiles repository
func isDotfilesDirectory(path string) bool {
	// Check for go.mod (our Go-based dotfiles tool)
	if _, err := os.Stat(filepath.Join(path, "go.mod")); err == nil {
		// Also check for our specific structure
		if _, err := os.Stat(filepath.Join(path, "internal", "config")); err == nil {
			return true
		}
	}
	
	// Check for other common dotfiles indicators
	indicators := []string{
		"config",
		"homebrew",
		"templates/config.yaml",
	}
	
	for _, indicator := range indicators {
		if _, err := os.Stat(filepath.Join(path, indicator)); err == nil {
			return true
		}
	}
	
	return false
}

// Save saves configuration to file
func (c *Config) Save(path string) error {
	// Expand tilde in path
	if strings.HasPrefix(path, "~/") {
		homeDir, err := os.UserHomeDir()
		if err != nil {
			return fmt.Errorf("failed to get home directory: %w", err)
		}
		path = filepath.Join(homeDir, path[2:])
	}

	// Create directory if it doesn't exist
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	// Marshal to YAML
	data, err := yaml.Marshal(c)
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	// Write to file
	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	return nil
}

// Validate validates the configuration
func (c *Config) Validate() error {
	// Validate global config
	if c.Global.DotfilesPath == "" {
		return fmt.Errorf("dotfiles_path cannot be empty")
	}
	
	if c.Global.LogLevel != "debug" && c.Global.LogLevel != "info" && 
	   c.Global.LogLevel != "warn" && c.Global.LogLevel != "error" {
		return fmt.Errorf("invalid log_level: %s", c.Global.LogLevel)
	}

	// Validate stow packages
	for i, pkg := range c.Stow.Packages {
		if pkg.Name == "" {
			return fmt.Errorf("stow package %d: name cannot be empty", i)
		}
		if pkg.Target == "" {
			return fmt.Errorf("stow package %s: target cannot be empty", pkg.Name)
		}
	}

	return nil
}

// ExpandVariables expands environment variables in configuration values
func (c *Config) ExpandVariables() error {
	// Expand variables in stow packages
	for i := range c.Stow.Packages {
		c.Stow.Packages[i].Target = os.ExpandEnv(c.Stow.Packages[i].Target)
	}

	// Expand variables in rsync sources
	for i := range c.Rsync.Sources {
		c.Rsync.Sources[i].Target = os.ExpandEnv(c.Rsync.Sources[i].Target)
	}

	// Expand dotfiles path
	c.Global.DotfilesPath = os.ExpandEnv(c.Global.DotfilesPath)

	return nil
}

// setDefaults sets default values for missing configuration fields
func (c *Config) setDefaults() error {
	defaults := DefaultConfig()

	// Set global defaults
	if c.Global.LogLevel == "" {
		c.Global.LogLevel = defaults.Global.LogLevel
	}
	if c.Global.BackupSuffix == "" {
		c.Global.BackupSuffix = defaults.Global.BackupSuffix
	}

	// Set TUI defaults
	if c.TUI.ColorScheme == "" {
		c.TUI.ColorScheme = defaults.TUI.ColorScheme
	}

	return nil
}