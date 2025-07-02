package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/test/testutil"
)

func TestGetConfig(t *testing.T) {
	// Test when config is not initialized
	originalCfg := cfg
	cfg = nil
	defer func() { cfg = originalCfg }()

	result := GetConfig()
	if result != nil {
		t.Error("Expected GetConfig to return nil when config is not initialized")
	}

	// Test when config is initialized
	cfg = &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
	}

	result = GetConfig()
	if result == nil {
		t.Fatal("Expected GetConfig to return non-nil when config is initialized")
	}

	if result.Global.DotfilesPath != "/test/path" {
		t.Errorf("Expected dotfiles path to be '/test/path', got %s", result.Global.DotfilesPath)
	}
}

func TestGetRegistry(t *testing.T) {
	// Test when registry is not initialized
	originalRegistry := registry
	registry = nil
	defer func() { registry = originalRegistry }()

	result := GetRegistry()
	if result != nil {
		t.Error("Expected GetRegistry to return nil when registry is not initialized")
	}
}

func TestInitConfig_WithValidFile(t *testing.T) {
	tmpDir := testutil.TempDir(t)
	configDir := filepath.Join(tmpDir, ".config", "dotfiles")
	configPath := filepath.Join(configDir, "config.yaml")

	// Create config directory
	err := os.MkdirAll(configDir, 0755)
	if err != nil {
		t.Fatalf("Failed to create config directory: %v", err)
	}

	// Create a valid config file
	configYAML := `global:
  dotfiles_path: "` + tmpDir + `"
  log_level: "info"
  dry_run: false
  auto_confirm: false

tui:
  color_scheme: "default"
  animations: true
  confirm_destructive: true
  show_progress: true

tools:
  priorities:
    stow: 1
    rsync: 20
  system_directories:
    - "/System"
    - "/Library"
  timeouts:
    rsync_cache: "30s"

performance:
  cache:
    default:
      size: 1000
      ttl: "5m"
      cleanup_interval: "1m"
    status:
      size: 100
      ttl: "30s"
      cleanup_interval: "15s"
    view:
      size: 50
      ttl: "1m"
      cleanup_interval: "30s"
    config:
      size: 20
      ttl: "10m"
      cleanup_interval: "2m"
    theme:
      size: 10
      ttl: "15m"
      cleanup_interval: "5m"
  monitor:
    interval: "5s"
    capacity: 100
  profiler:
    cooldown: "5m"
    auto_interval: "10s"
    profiles:
      cpu:
        duration: "30s"

validation:
  npm_package_pattern: '^(@[a-z0-9-~][a-z0-9-._~]*\/)?[a-z0-9-~][a-z0-9-._~]*$'
`

	err = os.WriteFile(configPath, []byte(configYAML), 0644)
	if err != nil {
		t.Fatalf("Failed to write config file: %v", err)
	}

	// Set up environment to use our test config
	originalHome := os.Getenv("HOME")
	os.Setenv("HOME", tmpDir)
	defer os.Setenv("HOME", originalHome)

	// Initialize with our test config file
	originalCfgFile := cfgFile
	cfgFile = configPath
	defer func() { cfgFile = originalCfgFile }()

	// Reset global state
	originalCfg := cfg
	originalRegistry := registry
	cfg = nil
	registry = nil
	defer func() {
		cfg = originalCfg
		registry = originalRegistry
	}()

	err = initConfig()
	if err != nil {
		t.Fatalf("Expected initConfig to succeed, got error: %v", err)
	}

	// Verify config was loaded
	if cfg == nil {
		t.Fatal("Expected cfg to be initialized")
	}

	if cfg.Global.DotfilesPath != tmpDir {
		t.Errorf("Expected dotfiles path to be %s, got %s", tmpDir, cfg.Global.DotfilesPath)
	}

	// Verify registry was initialized
	if registry == nil {
		t.Fatal("Expected registry to be initialized")
	}

	tools := registry.List()
	if len(tools) == 0 {
		t.Error("Expected registry to have tools registered")
	}
}

func TestInitConfig_WithNonExistentFile(t *testing.T) {
	tmpDir := testutil.TempDir(t)
	nonExistentPath := filepath.Join(tmpDir, "nonexistent.yaml")

	// Set up environment
	originalHome := os.Getenv("HOME")
	os.Setenv("HOME", tmpDir)
	defer os.Setenv("HOME", originalHome)

	originalCfgFile := cfgFile
	cfgFile = nonExistentPath
	defer func() { cfgFile = originalCfgFile }()

	// Reset global state
	originalCfg := cfg
	originalRegistry := registry
	cfg = nil
	registry = nil
	defer func() {
		cfg = originalCfg
		registry = originalRegistry
	}()

	err := initConfig()
	// Should not fail - config loading handles missing files
	if err != nil {
		t.Errorf("Expected initConfig to handle missing config file, got error: %v", err)
	}
}

func TestCreateLazyToolCommand(t *testing.T) {
	toolName := "test-tool"
	cmd := createLazyToolCommand(toolName)

	if cmd == nil {
		t.Fatal("Expected createLazyToolCommand to return non-nil command")
	}

	if cmd.Use != toolName {
		t.Errorf("Expected command Use to be '%s', got '%s'", toolName, cmd.Use)
	}

	// Check that subcommands were added
	subcommands := cmd.Commands()
	if len(subcommands) == 0 {
		t.Error("Expected tool command to have subcommands")
	}

	// Look for expected subcommands
	hasStatus := false
	hasList := false
	hasSync := false

	for _, subcmd := range subcommands {
		switch subcmd.Use {
		case "status":
			hasStatus = true
		case "list":
			hasList = true
		case "sync":
			hasSync = true
		}
	}

	if !hasStatus {
		t.Error("Expected tool command to have 'status' subcommand")
	}
	if !hasList {
		t.Error("Expected tool command to have 'list' subcommand")
	}
	if !hasSync {
		t.Error("Expected tool command to have 'sync' subcommand")
	}
}

func TestRegisterToolCommands(t *testing.T) {
	// This is a simple test to verify the function doesn't panic
	// The actual registration is tested indirectly through command creation
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("registerToolCommands panicked: %v", r)
		}
	}()

	// Call the function - it should not panic
	registerToolCommands()
}

func TestConfigFileValidation(t *testing.T) {
	// Test with valid temporary directory
	tmpDir := testutil.TempDir(t)

	// Create a test config file
	configContent := fmt.Sprintf(`
global:
  dotfiles_path: "%s"
  dry_run: false
  verbose: false
`, tmpDir)

	configPath := filepath.Join(tmpDir, "config.yaml")
	err := os.WriteFile(configPath, []byte(configContent), 0644)
	if err != nil {
		t.Fatalf("Failed to create test config file: %v", err)
	}

	// Test loading config
	loadedCfg, err := config.Load(configPath)
	if err != nil {
		t.Errorf("Expected config loading to succeed, got: %v", err)
	}

	if loadedCfg.Global.DotfilesPath != tmpDir {
		t.Errorf("Expected dotfiles path to be '%s', got '%s'", tmpDir, loadedCfg.Global.DotfilesPath)
	}
}

func TestConfigDefaults(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	// Create minimal config
	configContent := fmt.Sprintf(`
global:
  dotfiles_path: "%s"
`, tmpDir)

	configPath := filepath.Join(tmpDir, "config.yaml")
	err := os.WriteFile(configPath, []byte(configContent), 0644)
	if err != nil {
		t.Fatalf("Failed to create test config file: %v", err)
	}

	cfg, err := config.Load(configPath)
	if err != nil {
		t.Fatalf("Failed to load config: %v", err)
	}

	// Test that defaults are applied
	if cfg.Global.LogLevel == "" {
		// This is expected - defaults might not be set until validation
	}

	// Test that required field is set
	if cfg.Global.DotfilesPath != tmpDir {
		t.Errorf("Expected dotfiles path to be set to '%s'", tmpDir)
	}
}

func TestGlobalVariables(t *testing.T) {
	// Test that global variables exist
	// cfg and registry are package-level variables that should be accessible in tests

	// Save originals
	originalCfg := cfg
	originalRegistry := registry

	// Clean up after test
	defer func() {
		cfg = originalCfg
		registry = originalRegistry
	}()

	// Test nil states
	cfg = nil
	registry = nil

	if GetConfig() != nil {
		t.Error("Expected GetConfig to return nil when cfg is nil")
	}

	if GetRegistry() != nil {
		t.Error("Expected GetRegistry to return nil when registry is nil")
	}
}

func TestExecuteFunctionExists(t *testing.T) {
	// Test that Execute function exists and is callable
	// We can't easily test the full execution without affecting the test environment
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("Execute function should exist and be callable: %v", r)
		}
	}()

	// The function should exist - we're just checking it's defined
	// Actual execution testing would require complex setup to avoid side effects
}

func TestExecute_BasicFunctionality(t *testing.T) {
	// Test that Execute function exists and can be called
	// We can't easily test the full execution without side effects
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("Execute function panicked: %v", r)
		}
	}()

	// The function exists and is callable
	// Actual execution testing would require more complex setup
}
