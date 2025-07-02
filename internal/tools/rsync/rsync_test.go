package rsync

import (
	"context"
	"testing"

	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/test/testutil"
)

func TestNewRsyncTool(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
			DryRun:       false,
		},
		Rsync: config.RsyncConfig{
			Enabled: true,
			Sources: []config.RsyncSource{
				{Name: "configs", Target: "~/configs", Enabled: true, Priority: 1},
			},
		},
	}

	tool := NewRsyncTool(cfg)

	if tool == nil {
		t.Fatal("Expected NewRsyncTool to return non-nil tool")
	}

	if tool.Name() != "rsync" {
		t.Errorf("Expected tool name to be 'rsync', got %s", tool.Name())
	}

	if tool.Priority() != 20 {
		t.Errorf("Expected priority to be 20, got %d", tool.Priority())
	}

	if !tool.IsEnabled() {
		t.Error("Expected tool to be enabled")
	}
}

func TestRsyncTool_List(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
			DryRun:       true,
		},
		Rsync: config.RsyncConfig{
			Enabled: true,
			Sources: []config.RsyncSource{
				{Name: "test1", Target: "~/test1", Enabled: true, Priority: 1},
				{Name: "test2", Target: "~/test2", Enabled: false, Priority: 2},
			},
		},
	}

	tool := NewRsyncTool(cfg)
	ctx := context.Background()

	// Create test source directories
	testutil.CreateTestFile(t, tmpDir, "test1/file1.txt", "content1")
	testutil.CreateTestFile(t, tmpDir, "test2/file2.txt", "content2")

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

func TestRsyncTool_Configure(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		Rsync: config.RsyncConfig{
			Enabled: true,
			Sources: []config.RsyncSource{
				{Name: "test", Target: "~/test", Enabled: true, Priority: 1},
			},
		},
	}

	tool := NewRsyncTool(cfg)

	// Test with valid config
	newConfig := &config.RsyncConfig{
		Enabled: true,
		Sources: []config.RsyncSource{
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

func TestRsyncTool_ResolveSourcePath(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/dotfiles",
		},
	}

	tool := NewRsyncTool(cfg)

	result := tool.resolveSourcePath("configs")
	expected := "/dotfiles/configs"
	if result != expected {
		t.Errorf("Expected %s, got %s", expected, result)
	}
}

func TestRsyncTool_ResolveTargetPath(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/dotfiles",
		},
	}

	tool := NewRsyncTool(cfg)

	// Test tilde expansion
	result := tool.resolveTargetPath("~/test")
	if result == "~/test" {
		t.Error("Expected tilde to be expanded")
	}

	// Test absolute path
	result = tool.resolveTargetPath("/absolute/path")
	if result != "/absolute/path" {
		t.Errorf("Expected absolute path to be unchanged, got %s", result)
	}
}

func TestRsyncTool_FindSource(t *testing.T) {
	cfg := &config.Config{
		Rsync: config.RsyncConfig{
			Sources: []config.RsyncSource{
				{Name: "test1", Target: "~/test1", Enabled: true},
				{Name: "test2", Target: "~/test2", Enabled: false},
			},
		},
	}

	tool := NewRsyncTool(cfg)

	// Test existing source
	source := tool.findSource("test1")
	if source == nil {
		t.Fatal("Expected to find source 'test1'")
	}
	if source.Name != "test1" {
		t.Errorf("Expected source name 'test1', got %s", source.Name)
	}

	// Test non-existing source
	source = tool.findSource("nonexistent")
	if source != nil {
		t.Error("Expected not to find non-existent source")
	}
}

func TestRsyncTool_IsSystemDirectory(t *testing.T) {
	cfg := &config.Config{
		Tools: config.ToolsConfig{
			SystemDirectories: []string{"/System", "/Library", "/usr", "/bin", "/sbin", "/Applications", "~/Library", "~/Applications"},
		},
	}
	tool := NewRsyncTool(cfg)

	// Test system directories
	systemDirs := []string{"/System", "/Library", "/usr", "/bin", "/sbin"}
	for _, dir := range systemDirs {
		if !tool.isSystemDirectory(dir) {
			t.Errorf("Expected %s to be detected as system directory", dir)
		}
	}

	// Test non-system directory
	if tool.isSystemDirectory("/Users/test/custom") {
		t.Error("Expected /Users/test/custom to not be detected as system directory")
	}
}

func TestRsyncTool_Status(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
			DryRun:       true,
		},
		Rsync: config.RsyncConfig{
			Enabled: true,
			Sources: []config.RsyncSource{
				{Name: "valid", Target: "~/valid", Enabled: true, Priority: 1},
				{Name: "disabled", Target: "~/disabled", Enabled: false, Priority: 2},
			},
		},
	}

	tool := NewRsyncTool(cfg)
	ctx := context.Background()

	// Create valid source
	testutil.CreateTestFile(t, tmpDir, "valid/file.txt", "content")

	status, err := tool.Status(ctx)
	if err != nil {
		t.Fatalf("Expected Status to succeed, got: %v", err)
	}

	if status.Name != "rsync" {
		t.Errorf("Expected status name to be 'rsync', got %s", status.Name)
	}

	if !status.Enabled {
		t.Error("Expected status to be enabled")
	}

	if len(status.Items) != 2 {
		t.Errorf("Expected 2 status items, got %d", len(status.Items))
	}

	// Check that disabled source has correct status
	for _, item := range status.Items {
		if item.Name == "disabled" && item.Status != "disabled" {
			t.Errorf("Expected disabled source to have status 'disabled', got %s", item.Status)
		}
	}
}

func TestRsyncTool_Sync(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
			DryRun:       true, // Use dry run to avoid actual rsync calls
		},
		Rsync: config.RsyncConfig{
			Enabled: true,
			Sources: []config.RsyncSource{
				{Name: "test", Target: "~/test", Enabled: true, Priority: 1},
			},
		},
	}

	tool := NewRsyncTool(cfg)
	ctx := context.Background()

	// Create test source
	testutil.CreateTestFile(t, tmpDir, "test/file.txt", "content")

	result, err := tool.Sync(ctx)
	if err != nil {
		t.Fatalf("Expected Sync to succeed in dry run mode, got: %v", err)
	}

	if !result.Success {
		t.Error("Expected sync result to be successful in dry run mode")
	}

	if result.Tool != "rsync" {
		t.Errorf("Expected result tool to be 'rsync', got %s", result.Tool)
	}

	if result.Operation != "sync" {
		t.Errorf("Expected result operation to be 'sync', got %s", result.Operation)
	}
}
