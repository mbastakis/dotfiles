package config

import (
	"path/filepath"
	"testing"

	"github.com/mbastakis/dotfiles/test/testutil"
)

func TestDefaultConfig(t *testing.T) {
	config := DefaultConfig()

	if config == nil {
		t.Fatal("Expected DefaultConfig to return non-nil config")
	}

	// Test default values
	if config.Global.LogLevel != "info" {
		t.Errorf("Expected default log level to be 'info', got %s", config.Global.LogLevel)
	}

	if config.Global.DryRun != false {
		t.Error("Expected default dry run to be false")
	}

	if config.TUI.ColorScheme != "default" {
		t.Errorf("Expected default color scheme to be 'default', got %s", config.TUI.ColorScheme)
	}

	if !config.TUI.Animations {
		t.Error("Expected default animations to be true")
	}
}

func TestLoad_WithValidFile(t *testing.T) {
	tmpDir := testutil.TempDir(t)
	configPath := filepath.Join(tmpDir, "config.yaml")

	configYAML := `global:
  dotfiles_path: "/test/path"
  log_level: "debug"
  dry_run: true
  auto_confirm: true

tui:
  color_scheme: "light"
  animations: false
  confirm_destructive: false
  show_progress: false

stow:
  packages:
    - name: "test-package"
      target: "/custom/target"
      enabled: true
      priority: 1

homebrew:
  auto_update: false
  categories:
    core:
      enabled: false
      brewfile: "test/Brewfile"

npm:
  auto_install: false
  auto_update: false
  global_packages: ["test-package"]`

	testutil.CreateTestFile(t, tmpDir, "config.yaml", configYAML)

	config, err := Load(configPath)
	if err != nil {
		t.Fatalf("Expected Load to succeed, got: %v", err)
	}

	// Test loaded values
	if config.Global.DotfilesPath != "/test/path" {
		t.Errorf("Expected dotfiles path to be '/test/path', got %s", config.Global.DotfilesPath)
	}

	if config.Global.LogLevel != "debug" {
		t.Errorf("Expected log level to be 'debug', got %s", config.Global.LogLevel)
	}

	if !config.Global.DryRun {
		t.Error("Expected dry run to be true")
	}

	if config.TUI.ColorScheme != "light" {
		t.Errorf("Expected color scheme to be 'light', got %s", config.TUI.ColorScheme)
	}

	if config.TUI.Animations {
		t.Error("Expected animations to be false")
	}
}

func TestLoad_WithNonExistentFile(t *testing.T) {
	config, err := Load("/nonexistent/config.yaml")
	if err != nil {
		t.Fatalf("Expected Load to return default config for non-existent file, got: %v", err)
	}

	// Should return default config
	if config.Global.LogLevel != "info" {
		t.Errorf("Expected default log level, got %s", config.Global.LogLevel)
	}
}

func TestLoad_WithInvalidYAML(t *testing.T) {
	tmpDir := testutil.TempDir(t)
	configPath := filepath.Join(tmpDir, "config.yaml")

	invalidYAML := `global:
  dotfiles_path: "/test/path"
  - invalid syntax`

	testutil.CreateTestFile(t, tmpDir, "config.yaml", invalidYAML)

	_, err := loadFromPath(configPath)
	if err == nil {
		t.Fatal("Expected loadFromPath to fail with invalid YAML")
	}
}

func TestSave(t *testing.T) {
	tmpDir := testutil.TempDir(t)
	configPath := filepath.Join(tmpDir, "config.yaml")

	config := DefaultConfig()
	config.Global.DotfilesPath = "/custom/path"
	config.Global.LogLevel = "debug"
	config.TUI.ColorScheme = "cyberpunk"

	err := config.Save(configPath)
	if err != nil {
		t.Fatalf("Expected Save to succeed, got: %v", err)
	}

	// Verify file was created
	testutil.AssertFileExists(t, configPath)

	// Verify content
	testutil.AssertFileContains(t, configPath, "/custom/path")
	testutil.AssertFileContains(t, configPath, "debug")
	testutil.AssertFileContains(t, configPath, "cyberpunk")

	// Load the saved config and verify
	loadedConfig, err := Load(configPath)
	if err != nil {
		t.Fatalf("Expected to load saved config, got: %v", err)
	}

	if loadedConfig.Global.DotfilesPath != "/custom/path" {
		t.Errorf("Expected loaded dotfiles path to be '/custom/path', got %s", loadedConfig.Global.DotfilesPath)
	}

	if loadedConfig.Global.LogLevel != "debug" {
		t.Errorf("Expected loaded log level to be 'debug', got %s", loadedConfig.Global.LogLevel)
	}

	if loadedConfig.TUI.ColorScheme != "cyberpunk" {
		t.Errorf("Expected loaded color scheme to be 'cyberpunk', got %s", loadedConfig.TUI.ColorScheme)
	}
}

func TestValidate(t *testing.T) {
	tests := []struct {
		name        string
		config      *Config
		expectError bool
		errorMsg    string
	}{
		{
			name:        "valid config",
			config:      DefaultConfig(),
			expectError: false,
		},
		{
			name: "empty dotfiles path",
			config: &Config{
				Global: GlobalConfig{
					DotfilesPath: "",
					LogLevel:     "info",
				},
				Performance: PerformanceConfig{
					Cache: CacheConfig{
						Default: CacheSetting{Size: 1000, TTL: "5m", CleanupInterval: "1m"},
						Status:  CacheSetting{Size: 100, TTL: "30s", CleanupInterval: "15s"},
						View:    CacheSetting{Size: 50, TTL: "1m", CleanupInterval: "30s"},
						Config:  CacheSetting{Size: 20, TTL: "10m", CleanupInterval: "2m"},
						Theme:   CacheSetting{Size: 10, TTL: "15m", CleanupInterval: "5m"},
					},
					Monitor: MonitorConfig{Interval: "5s", Capacity: 100},
					Profiler: ProfilerConfig{
						Cooldown:     "5m",
						AutoInterval: "10s",
						Profiles: map[string]ProfileSetting{
							"cpu": {Duration: "30s"},
						},
					},
				},
				Validation: ValidationConfig{NPMPackagePattern: "^(@[a-z0-9-~][a-z0-9-._~]*\\/)?[a-z0-9-~][a-z0-9-._~]*$"},
			},
			expectError: true,
			errorMsg:    "dotfiles_path cannot be empty",
		},
		{
			name: "invalid log level",
			config: &Config{
				Global: GlobalConfig{
					DotfilesPath: "/valid/path",
					LogLevel:     "invalid",
				},
			},
			expectError: true,
			errorMsg:    "invalid log_level",
		},
		{
			name: "empty package name",
			config: &Config{
				Global: GlobalConfig{
					DotfilesPath: "/valid/path",
					LogLevel:     "info",
				},
				Stow: StowConfig{
					Packages: []StowPackage{
						{Name: "", Target: "/target", Enabled: true},
					},
				},
				Performance: PerformanceConfig{
					Cache: CacheConfig{
						Default: CacheSetting{Size: 1000, TTL: "5m", CleanupInterval: "1m"},
						Status:  CacheSetting{Size: 100, TTL: "30s", CleanupInterval: "15s"},
						View:    CacheSetting{Size: 50, TTL: "1m", CleanupInterval: "30s"},
						Config:  CacheSetting{Size: 20, TTL: "10m", CleanupInterval: "2m"},
						Theme:   CacheSetting{Size: 10, TTL: "15m", CleanupInterval: "5m"},
					},
					Monitor: MonitorConfig{Interval: "5s", Capacity: 100},
					Profiler: ProfilerConfig{
						Cooldown:     "5m",
						AutoInterval: "10s",
						Profiles: map[string]ProfileSetting{
							"cpu": {Duration: "30s"},
						},
					},
				},
				Validation: ValidationConfig{NPMPackagePattern: "^(@[a-z0-9-~][a-z0-9-._~]*\\/)?[a-z0-9-~][a-z0-9-._~]*$"},
			},
			expectError: true,
			errorMsg:    "name cannot be empty",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.config.Validate()

			if tt.expectError {
				if err == nil {
					t.Fatalf("Expected validation to fail for %s", tt.name)
				}
				if tt.errorMsg != "" && !contains(err.Error(), tt.errorMsg) {
					t.Errorf("Expected error to contain '%s', got: %v", tt.errorMsg, err)
				}
			} else {
				if err != nil {
					t.Fatalf("Expected validation to succeed for %s, got: %v", tt.name, err)
				}
			}
		})
	}
}

func TestExpandVariables(t *testing.T) {
	config := &Config{
		Global: GlobalConfig{
			DotfilesPath: "$HOME/dotfiles",
		},
		Stow: StowConfig{
			Packages: []StowPackage{
				{Name: "test", Target: "$HOME/.config", Enabled: true},
			},
		},
		Rsync: RsyncConfig{
			Sources: []RsyncSource{
				{Name: "test", Target: "$HOME/target", Enabled: true},
			},
		},
	}

	err := config.ExpandVariables()
	if err != nil {
		t.Fatalf("Expected ExpandVariables to succeed, got: %v", err)
	}

	// Variables should be expanded (though we can't test exact values without knowing HOME)
	if config.Global.DotfilesPath == "$HOME/dotfiles" {
		t.Error("Expected dotfiles path to be expanded")
	}

	if config.Stow.Packages[0].Target == "$HOME/.config" {
		t.Error("Expected stow target to be expanded")
	}

	if config.Rsync.Sources[0].Target == "$HOME/target" {
		t.Error("Expected rsync target to be expanded")
	}
}

func TestSetDefaults(t *testing.T) {
	config := &Config{
		Global: GlobalConfig{
			DotfilesPath: "/test/path",
			// LogLevel empty - should be set to default
		},
		TUI: TUIConfig{
			// ColorScheme empty - should be set to default
		},
	}

	err := config.setDefaults()
	if err != nil {
		t.Fatalf("Expected setDefaults to succeed, got: %v", err)
	}

	if config.Global.LogLevel != "info" {
		t.Errorf("Expected log level to be set to default 'info', got %s", config.Global.LogLevel)
	}

	if config.TUI.ColorScheme != "default" {
		t.Errorf("Expected color scheme to be set to default 'default', got %s", config.TUI.ColorScheme)
	}

}

// Helper function for string contains check
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(substr) == 0 || containsHelper(s, substr))
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
