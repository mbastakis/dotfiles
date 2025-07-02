package stow

import (
	"context"
	"testing"

	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/test/testutil"
)

func TestNewStowTool(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
			DryRun:       false,
		},
		Stow: config.StowConfig{
			Packages: []config.StowPackage{
				{Name: "test", Target: "~/test", Enabled: true, Priority: 1},
			},
		},
	}

	tool := NewStowTool(cfg)

	if tool == nil {
		t.Fatal("Expected NewStowTool to return non-nil tool")
	}

	if tool.Name() != "stow" {
		t.Errorf("Expected tool name to be 'stow', got %s", tool.Name())
	}

	if tool.Priority() != 1 {
		t.Errorf("Expected priority to be 1, got %d", tool.Priority())
	}

	if !tool.IsEnabled() {
		t.Error("Expected tool to be enabled")
	}
}

func TestStowTool_List(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
			DryRun:       true,
		},
		Stow: config.StowConfig{
			Packages: []config.StowPackage{
				{Name: "test1", Target: "~/test1", Enabled: true, Priority: 1},
				{Name: "test2", Target: "~/test2", Enabled: false, Priority: 2},
			},
		},
	}

	tool := NewStowTool(cfg)
	ctx := context.Background()

	// Create test package directories
	testutil.CreateTestFile(t, tmpDir, "config/test1/file1.txt", "content1")
	testutil.CreateTestFile(t, tmpDir, "config/test2/file2.txt", "content2")

	items, err := tool.List(ctx)
	if err != nil {
		t.Fatalf("Expected List to succeed, got: %v", err)
	}

	if len(items) != 2 {
		t.Errorf("Expected 2 items, got %d", len(items))
	}

	// Check first item
	if items[0].Name != "test1" {
		t.Errorf("Expected first item name to be 'test1', got %s", items[0].Name)
	}

	if !items[0].Enabled {
		t.Error("Expected first item to be enabled")
	}

	// Check second item
	if items[1].Name != "test2" {
		t.Errorf("Expected second item name to be 'test2', got %s", items[1].Name)
	}

	if items[1].Enabled {
		t.Error("Expected second item to be disabled")
	}
}

func TestStowTool_Configure(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		Stow: config.StowConfig{
			Packages: []config.StowPackage{
				{Name: "test", Target: "~/test", Enabled: true, Priority: 1},
			},
		},
	}

	tool := NewStowTool(cfg)

	// Test with valid config
	newConfig := &config.StowConfig{
		Packages: []config.StowPackage{
			{Name: "new", Target: "~/new", Enabled: true, Priority: 1},
		},
	}

	err := tool.Configure(newConfig)
	if err != nil {
		t.Fatalf("Expected Configure to succeed, got: %v", err)
	}

	// Test with invalid config type
	err = tool.Configure("invalid")
	if err == nil {
		t.Fatal("Expected Configure to fail with invalid config type")
	}
}

func TestStowTool_ValidatePackage(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
		},
	}

	tool := NewStowTool(cfg)

	// Test valid package
	testutil.CreateTestFile(t, tmpDir, "config/valid/file.txt", "content")

	validPkg := config.StowPackage{
		Name:   "valid",
		Target: "~/target",
	}

	err := tool.validatePackage(validPkg)
	if err != nil {
		t.Errorf("Expected validation to succeed for valid package, got: %v", err)
	}

	// Test package with empty name
	emptyNamePkg := config.StowPackage{
		Name:   "",
		Target: "~/target",
	}

	err = tool.validatePackage(emptyNamePkg)
	if err == nil {
		t.Error("Expected validation to fail for package with empty name")
	}

	// Test package with empty target
	emptyTargetPkg := config.StowPackage{
		Name:   "test",
		Target: "",
	}

	err = tool.validatePackage(emptyTargetPkg)
	if err == nil {
		t.Error("Expected validation to fail for package with empty target")
	}

	// Test package that doesn't exist
	nonExistentPkg := config.StowPackage{
		Name:   "nonexistent",
		Target: "~/target",
	}

	err = tool.validatePackage(nonExistentPkg)
	if err == nil {
		t.Error("Expected validation to fail for non-existent package")
	}
}

func TestStowTool_ResolveTarget(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
		},
	}

	tool := NewStowTool(cfg)

	// Test tilde expansion
	resolved := tool.resolveTarget("~/test")
	if resolved == "~/test" {
		t.Error("Expected tilde to be expanded")
	}

	// Test that absolute paths are unchanged
	resolved = tool.resolveTarget("/absolute/path")
	if resolved != "/absolute/path" {
		t.Errorf("Expected absolute path to be unchanged, got %s", resolved)
	}
}

func TestStowTool_IsPackageLinked(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
		},
	}

	tool := NewStowTool(cfg)

	// Test with non-existent package
	pkg := config.StowPackage{
		Name:   "nonexistent",
		Target: tmpDir,
	}

	linked, err := tool.isPackageLinked(pkg)
	if err == nil {
		t.Error("Expected error for non-existent package check")
	}
	if linked {
		t.Error("Expected non-existent package to not be linked")
	}
}

func TestStowTool_EnableDisable(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test",
		},
	}

	tool := NewStowTool(cfg)

	// Test initial state
	if !tool.IsEnabled() {
		t.Error("Expected tool to be enabled by default")
	}

	// Test that we can access enabled state
	enabled := tool.enabled
	if !enabled {
		t.Error("Expected enabled field to be true")
	}
}

func TestStowTool_ConfigurablePriority(t *testing.T) {
	// Test with custom priority
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test",
		},
		Tools: config.ToolsConfig{
			Priorities: map[string]int{
				"stow": 5,
			},
		},
	}

	tool := NewStowTool(cfg)

	if tool.Priority() != 5 {
		t.Errorf("Expected priority to be 5, got %d", tool.Priority())
	}

	// Test with no priority set (should use default)
	cfgDefault := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test",
		},
		Tools: config.ToolsConfig{
			Priorities: map[string]int{},
		},
	}

	toolDefault := NewStowTool(cfgDefault)

	if toolDefault.Priority() != 1 {
		t.Errorf("Expected default priority to be 1, got %d", toolDefault.Priority())
	}
}

func TestStowTool_DryRunMode(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test",
			DryRun:       true,
		},
	}

	tool := NewStowTool(cfg)

	// Test that dry run state is preserved
	if !tool.dryRun {
		t.Error("Expected tool to be in dry run mode")
	}

	// Test non-dry run mode
	cfg.Global.DryRun = false
	toolNoDryRun := NewStowTool(cfg)

	if toolNoDryRun.dryRun {
		t.Error("Expected tool to not be in dry run mode")
	}
}

func TestStowTool_PackageManagement(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		Stow: config.StowConfig{
			Packages: []config.StowPackage{
				{Name: "vim", Target: "~/", Enabled: true, Priority: 1},
				{Name: "zsh", Target: "~/", Enabled: false, Priority: 2},
				{Name: "git", Target: "~/", Enabled: true, Priority: 3},
			},
		},
	}

	tool := NewStowTool(cfg)

	// Test number of packages
	if len(tool.config.Packages) != 3 {
		t.Errorf("Expected 3 packages, got %d", len(tool.config.Packages))
	}

	// Test specific packages
	expectedPackages := []string{"vim", "zsh", "git"}
	for i, expected := range expectedPackages {
		if tool.config.Packages[i].Name != expected {
			t.Errorf("Expected package %d to be '%s', got '%s'", i, expected, tool.config.Packages[i].Name)
		}
	}

	// Test enabled/disabled status
	if !tool.config.Packages[0].Enabled {
		t.Error("Expected vim package to be enabled")
	}

	if tool.config.Packages[1].Enabled {
		t.Error("Expected zsh package to be disabled")
	}

	if !tool.config.Packages[2].Enabled {
		t.Error("Expected git package to be enabled")
	}
}

func TestStowTool_EmptyPackages(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		Stow: config.StowConfig{
			Packages: []config.StowPackage{},
		},
	}

	tool := NewStowTool(cfg)

	if len(tool.config.Packages) != 0 {
		t.Errorf("Expected 0 packages, got %d", len(tool.config.Packages))
	}

	// Should still be a valid tool
	if tool.Name() != "stow" {
		t.Errorf("Expected tool name to be 'stow', got %s", tool.Name())
	}
}

func TestStowTool_PackagePriorities(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		Stow: config.StowConfig{
			Packages: []config.StowPackage{
				{Name: "high", Target: "~/", Enabled: true, Priority: 1},
				{Name: "medium", Target: "~/", Enabled: true, Priority: 5},
				{Name: "low", Target: "~/", Enabled: true, Priority: 10},
			},
		},
	}

	tool := NewStowTool(cfg)

	// Test that priorities are preserved
	if tool.config.Packages[0].Priority != 1 {
		t.Errorf("Expected first package priority to be 1, got %d", tool.config.Packages[0].Priority)
	}

	if tool.config.Packages[1].Priority != 5 {
		t.Errorf("Expected second package priority to be 5, got %d", tool.config.Packages[1].Priority)
	}

	if tool.config.Packages[2].Priority != 10 {
		t.Errorf("Expected third package priority to be 10, got %d", tool.config.Packages[2].Priority)
	}
}

func TestStowTool_PackageTargets(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		Stow: config.StowConfig{
			Packages: []config.StowPackage{
				{Name: "vim", Target: "~/", Enabled: true, Priority: 1},
				{Name: "config", Target: "~/.config", Enabled: true, Priority: 2},
				{Name: "local", Target: "~/.local", Enabled: true, Priority: 3},
			},
		},
	}

	tool := NewStowTool(cfg)

	// Test that targets are preserved
	expectedTargets := []string{"~/", "~/.config", "~/.local"}
	for i, expected := range expectedTargets {
		if tool.config.Packages[i].Target != expected {
			t.Errorf("Expected package %d target to be '%s', got '%s'", i, expected, tool.config.Packages[i].Target)
		}
	}
}

func TestStowTool_EnabledState(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		Stow: config.StowConfig{
			Packages: []config.StowPackage{
				{Name: "vim", Target: "~/", Enabled: true, Priority: 1},
			},
		},
	}

	tool := NewStowTool(cfg)

	// Test that tool is enabled by default
	if !tool.enabled {
		t.Error("Expected stow tool to be enabled by default")
	}

	if !tool.IsEnabled() {
		t.Error("Expected IsEnabled to return true")
	}
}

func TestStowTool_Fields(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		Stow: config.StowConfig{
			Packages: []config.StowPackage{
				{Name: "vim", Target: "~/", Enabled: true, Priority: 1},
			},
		},
	}

	tool := NewStowTool(cfg)

	// Test that all fields are properly set
	if tool.config == nil {
		t.Error("Expected config field to be set")
	}

	if tool.dotfilesPath != "/test/path" {
		t.Errorf("Expected dotfilesPath to be '/test/path', got '%s'", tool.dotfilesPath)
	}

	if !tool.IsEnabled() {
		t.Error("Expected tool to be enabled by default")
	}
}
