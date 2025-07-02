package apps

import (
	"context"
	"os"
	"testing"

	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/test/testutil"
)

func TestNewAppsTool(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
			DryRun:       false,
		},
		Apps: config.AppsConfig{
			"test-app": config.AppConfig{
				Enabled: true,
				Scripts: []string{"scripts/install.sh", "scripts/configure.sh"},
			},
		},
	}

	tool := NewAppsTool(cfg)

	if tool == nil {
		t.Fatal("Expected NewAppsTool to return non-nil tool")
	}

	if tool.Name() != "apps" {
		t.Errorf("Expected tool name to be 'apps', got %s", tool.Name())
	}

	if tool.Priority() != 40 {
		t.Errorf("Expected priority to be 40, got %d", tool.Priority())
	}

	if !tool.IsEnabled() {
		t.Error("Expected tool to be enabled")
	}
}

func TestAppsTool_IsEnabled(t *testing.T) {
	// Test with empty config
	cfg := &config.Config{
		Apps: config.AppsConfig{},
	}
	tool := NewAppsTool(cfg)
	if tool.IsEnabled() {
		t.Error("Expected tool to be disabled with empty config")
	}

	// Test with nil config
	cfg.Apps = nil
	tool = NewAppsTool(cfg)
	if tool.IsEnabled() {
		t.Error("Expected tool to be disabled with nil config")
	}

	// Test with apps
	cfg.Apps = config.AppsConfig{
		"test-app": config.AppConfig{
			Enabled: true,
			Scripts: []string{"script.sh"},
		},
	}
	tool = NewAppsTool(cfg)
	if !tool.IsEnabled() {
		t.Error("Expected tool to be enabled with apps config")
	}
}

func TestAppsTool_List(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
			DryRun:       true,
		},
		Apps: config.AppsConfig{
			"test-app1": config.AppConfig{
				Enabled: true,
				Scripts: []string{"scripts/app1.sh"},
			},
			"test-app2": config.AppConfig{
				Enabled: false,
				Scripts: []string{"scripts/app2.sh"},
			},
		},
	}

	tool := NewAppsTool(cfg)
	ctx := context.Background()

	// Create test scripts
	testutil.CreateTestFile(t, tmpDir, "scripts/app1.sh", "#!/bin/bash\necho 'app1'")
	testutil.CreateTestFile(t, tmpDir, "scripts/app2.sh", "#!/bin/bash\necho 'app2'")

	// Make scripts executable
	scriptPath1 := tmpDir + "/scripts/app1.sh"
	scriptPath2 := tmpDir + "/scripts/app2.sh"
	os.Chmod(scriptPath1, 0755)
	os.Chmod(scriptPath2, 0755)

	items, err := tool.List(ctx)
	if err != nil {
		t.Fatalf("Expected List to succeed, got: %v", err)
	}

	if len(items) != 2 {
		t.Errorf("Expected 2 items, got %d", len(items))
	}

	// Check items
	itemMap := make(map[string]bool)
	enabledMap := make(map[string]bool)
	for _, item := range items {
		itemMap[item.Name] = true
		enabledMap[item.Name] = item.Enabled
	}

	if !itemMap["test-app1"] || !itemMap["test-app2"] {
		t.Error("Expected to find both test-app1 and test-app2")
	}

	if !enabledMap["test-app1"] {
		t.Error("Expected test-app1 to be enabled")
	}

	if enabledMap["test-app2"] {
		t.Error("Expected test-app2 to be disabled")
	}
}

func TestAppsTool_Configure(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		Apps: config.AppsConfig{
			"test-app": config.AppConfig{
				Enabled: true,
				Scripts: []string{"script.sh"},
			},
		},
	}

	tool := NewAppsTool(cfg)

	// Test with valid config
	newConfig := &config.AppsConfig{
		"new-app": config.AppConfig{
			Enabled: true,
			Scripts: []string{"new-script.sh"},
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

func TestAppsTool_ResolveScriptPath(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/dotfiles",
		},
	}

	tool := NewAppsTool(cfg)

	// Test relative path
	result := tool.resolveScriptPath("scripts/install.sh")
	expected := "/dotfiles/scripts/install.sh"
	if result != expected {
		t.Errorf("Expected %s, got %s", expected, result)
	}

	// Test absolute path
	result = tool.resolveScriptPath("/absolute/path/script.sh")
	expected = "/absolute/path/script.sh"
	if result != expected {
		t.Errorf("Expected %s, got %s", expected, result)
	}
}

func TestAppsTool_ValidateScript(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
		},
	}

	tool := NewAppsTool(cfg)

	// Create test script
	scriptContent := "#!/bin/bash\necho 'test'"
	testutil.CreateTestFile(t, tmpDir, "test-script.sh", scriptContent)
	scriptPath := tmpDir + "/test-script.sh"

	// Test non-executable script
	err := tool.validateScript(scriptPath)
	if err == nil {
		t.Error("Expected validation to fail for non-executable script")
	}

	// Make script executable
	os.Chmod(scriptPath, 0755)

	// Test executable script
	err = tool.validateScript(scriptPath)
	if err != nil {
		t.Errorf("Expected validation to succeed for executable script, got: %v", err)
	}

	// Test non-existent script
	err = tool.validateScript("/nonexistent/script.sh")
	if err == nil {
		t.Error("Expected validation to fail for non-existent script")
	}
}

func TestAppsTool_Status(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
			DryRun:       true,
		},
		Apps: config.AppsConfig{
			"valid-app": config.AppConfig{
				Enabled: true,
				Scripts: []string{"scripts/valid.sh"},
			},
			"disabled-app": config.AppConfig{
				Enabled: false,
				Scripts: []string{"scripts/disabled.sh"},
			},
			"invalid-app": config.AppConfig{
				Enabled: true,
				Scripts: []string{"scripts/nonexistent.sh"},
			},
		},
	}

	tool := NewAppsTool(cfg)
	ctx := context.Background()

	// Create valid script
	testutil.CreateTestFile(t, tmpDir, "scripts/valid.sh", "#!/bin/bash\necho 'valid'")
	testutil.CreateTestFile(t, tmpDir, "scripts/disabled.sh", "#!/bin/bash\necho 'disabled'")

	// Make scripts executable
	os.Chmod(tmpDir+"/scripts/valid.sh", 0755)
	os.Chmod(tmpDir+"/scripts/disabled.sh", 0755)

	status, err := tool.Status(ctx)
	if err != nil {
		t.Fatalf("Expected Status to succeed, got: %v", err)
	}

	if status.Name != "apps" {
		t.Errorf("Expected status name to be 'apps', got %s", status.Name)
	}

	if !status.Enabled {
		t.Error("Expected status to be enabled")
	}

	if len(status.Items) != 3 {
		t.Errorf("Expected 3 status items, got %d", len(status.Items))
	}

	// Check status of each app
	statusMap := make(map[string]string)
	for _, item := range status.Items {
		statusMap[item.Name] = item.Status
	}

	if statusMap["valid-app"] != "ready" {
		t.Errorf("Expected valid-app to have status 'ready', got %s", statusMap["valid-app"])
	}

	if statusMap["disabled-app"] != "disabled" {
		t.Errorf("Expected disabled-app to have status 'disabled', got %s", statusMap["disabled-app"])
	}

	if statusMap["invalid-app"] != "error" {
		t.Errorf("Expected invalid-app to have status 'error', got %s", statusMap["invalid-app"])
	}
}

func TestAppsTool_RunApps(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
			DryRun:       true, // Use dry run to avoid actually executing scripts
		},
		Apps: config.AppsConfig{
			"test-app": config.AppConfig{
				Enabled: true,
				Scripts: []string{"scripts/test.sh"},
			},
		},
	}

	tool := NewAppsTool(cfg)
	ctx := context.Background()

	// Create test script
	testutil.CreateTestFile(t, tmpDir, "scripts/test.sh", "#!/bin/bash\necho 'test executed'")
	os.Chmod(tmpDir+"/scripts/test.sh", 0755)

	// Test running apps
	result, err := tool.runApps(ctx, []string{"test-app"}, "install")
	if err != nil {
		t.Fatalf("Expected runApps to succeed in dry run mode, got: %v", err)
	}

	if !result.Success {
		t.Error("Expected result to be successful in dry run mode")
	}

	if result.Tool != "apps" {
		t.Errorf("Expected result tool to be 'apps', got %s", result.Tool)
	}

	if result.Operation != "install" {
		t.Errorf("Expected result operation to be 'install', got %s", result.Operation)
	}

	// Check executed apps
	if executed, ok := result.Details["executed"].([]string); ok {
		if len(executed) != 1 || executed[0] != "test-app" {
			t.Errorf("Expected executed to contain 'test-app', got %v", executed)
		}
	} else {
		t.Error("Expected executed details to be present")
	}
}

func TestAppsTool_Sync(t *testing.T) {
	tmpDir := testutil.TempDir(t)

	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: tmpDir,
			DryRun:       true,
		},
		Apps: config.AppsConfig{
			"app1": config.AppConfig{
				Enabled: true,
				Scripts: []string{"scripts/app1.sh"},
			},
			"app2": config.AppConfig{
				Enabled: false,
				Scripts: []string{"scripts/app2.sh"},
			},
		},
	}

	tool := NewAppsTool(cfg)
	ctx := context.Background()

	// Create test scripts
	testutil.CreateTestFile(t, tmpDir, "scripts/app1.sh", "#!/bin/bash\necho 'app1'")
	testutil.CreateTestFile(t, tmpDir, "scripts/app2.sh", "#!/bin/bash\necho 'app2'")
	os.Chmod(tmpDir+"/scripts/app1.sh", 0755)
	os.Chmod(tmpDir+"/scripts/app2.sh", 0755)

	result, err := tool.Sync(ctx)
	if err != nil {
		t.Fatalf("Expected Sync to succeed, got: %v", err)
	}

	if !result.Success {
		t.Error("Expected sync result to be successful")
	}

	if result.Operation != "sync" {
		t.Errorf("Expected result operation to be 'sync', got %s", result.Operation)
	}

	// Only enabled apps should be executed
	if executed, ok := result.Details["executed"].([]string); ok {
		if len(executed) != 1 || executed[0] != "app1" {
			t.Errorf("Expected only 'app1' to be executed, got %v", executed)
		}
	} else {
		t.Error("Expected executed details to be present")
	}
}

func TestAppsTool_Remove(t *testing.T) {
	cfg := &config.Config{
		Apps: config.AppsConfig{
			"test-app": config.AppConfig{
				Enabled: true,
				Scripts: []string{"script.sh"},
			},
		},
	}

	tool := NewAppsTool(cfg)
	ctx := context.Background()

	result, err := tool.Remove(ctx, []string{"test-app"})
	if err != nil {
		t.Fatalf("Expected Remove to succeed, got: %v", err)
	}

	if !result.Success {
		t.Error("Expected remove result to be successful")
	}

	if result.Operation != "remove" {
		t.Errorf("Expected result operation to be 'remove', got %s", result.Operation)
	}

	// Remove should indicate it's not supported
	if message, ok := result.Details["message"].(string); ok {
		if message != "remove operation not supported for custom apps" {
			t.Errorf("Expected unsupported message, got: %s", message)
		}
	} else {
		t.Error("Expected message in details")
	}
}
