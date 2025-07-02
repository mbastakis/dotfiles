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
