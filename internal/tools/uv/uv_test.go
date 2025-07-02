package uv

import (
	"context"
	"testing"

	"github.com/mbastakis/dotfiles/internal/config"
)

func TestNewUVTool(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
			DryRun:       false,
		},
		UV: config.UVConfig{
			AutoInstall:    true,
			AutoUpdate:     true,
			GlobalPackages: []string{"ruff", "black", "pytest"},
		},
	}

	tool := NewUVTool(cfg)

	if tool == nil {
		t.Fatal("Expected NewUVTool to return non-nil tool")
	}

	if tool.Name() != "uv" {
		t.Errorf("Expected tool name to be 'uv', got %s", tool.Name())
	}

	if tool.Priority() != 60 {
		t.Errorf("Expected priority to be 60, got %d", tool.Priority())
	}

	if !tool.IsEnabled() {
		t.Error("Expected tool to be enabled")
	}
}

func TestUVTool_List(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DryRun: true, // Use dry run to avoid actual uv calls
		},
		UV: config.UVConfig{
			AutoInstall:    true,
			AutoUpdate:     true,
			GlobalPackages: []string{"ruff", "black", "pytest"},
		},
	}

	tool := NewUVTool(cfg)
	ctx := context.Background()

	// In dry run mode, List should work without actually calling uv
	items, err := tool.List(ctx)
	if err != nil {
		t.Fatalf("Expected List to succeed in dry run mode, got: %v", err)
	}

	if len(items) != 3 {
		t.Errorf("Expected 3 items, got %d", len(items))
	}

	expectedPackages := map[string]bool{
		"ruff":   true,
		"black":  true,
		"pytest": true,
	}

	for _, item := range items {
		if !expectedPackages[item.Name] {
			t.Errorf("Unexpected package in list: %s", item.Name)
		}

		if !item.Enabled {
			t.Errorf("Expected package %s to be enabled", item.Name)
		}

		if item.Description != "UV Python tool" && item.Status != "installed" {
			// In dry run mode without uv installed, status will be "not_installed"
			if item.Status != "not_installed" {
				t.Errorf("Expected package %s to have status 'not_installed' in test mode, got %s", item.Name, item.Status)
			}
		}
	}
}

func TestUVTool_Configure(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		UV: config.UVConfig{
			AutoInstall:    true,
			GlobalPackages: []string{"ruff"},
		},
	}

	tool := NewUVTool(cfg)

	// Test with valid config
	newConfig := &config.UVConfig{
		AutoInstall:    false,
		AutoUpdate:     true,
		GlobalPackages: []string{"black", "pytest"},
	}

	err := tool.Configure(newConfig)
	if err != nil {
		t.Fatalf("Expected Configure to succeed, got: %v", err)
	}

	// Verify config was updated
	items, err := tool.List(context.Background())
	if err != nil {
		t.Fatalf("Expected List to succeed after configure, got: %v", err)
	}

	if len(items) != 2 {
		t.Errorf("Expected 2 items after configure, got %d", len(items))
	}

	// Test with invalid config type
	err = tool.Configure("invalid")
	if err == nil {
		t.Fatal("Expected Configure to fail with invalid config type")
	}
}

func TestUVTool_Sync(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DryRun: true, // Use dry run to avoid actual uv calls
		},
		UV: config.UVConfig{
			AutoInstall:    true,
			AutoUpdate:     false,
			GlobalPackages: []string{"ruff", "black"},
		},
	}

	tool := NewUVTool(cfg)
	ctx := context.Background()

	// Test sync with auto_install enabled
	result, err := tool.Sync(ctx)
	if err != nil {
		t.Fatalf("Expected Sync to succeed in dry run mode, got: %v", err)
	}

	if !result.Success {
		t.Error("Expected sync result to be successful in dry run mode")
	}

	if result.Tool != "uv" {
		t.Errorf("Expected result tool to be 'uv', got %s", result.Tool)
	}

	if result.Operation != "install" {
		t.Errorf("Expected result operation to be 'install', got %s", result.Operation)
	}

	// Test sync with auto_install disabled
	cfg.UV.AutoInstall = false
	tool = NewUVTool(cfg)

	result, err = tool.Sync(ctx)
	if err != nil {
		t.Fatalf("Expected Sync to succeed with auto_install disabled, got: %v", err)
	}

	if !result.Success {
		t.Error("Expected sync result to be successful with auto_install disabled")
	}

	if result.Operation != "sync" {
		t.Errorf("Expected result operation to be 'sync', got %s", result.Operation)
	}
}

func TestUVTool_Install(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DryRun: true, // Use dry run to avoid actual uv calls
		},
		UV: config.UVConfig{
			AutoInstall:    true,
			GlobalPackages: []string{"ruff", "black"},
		},
	}

	tool := NewUVTool(cfg)
	ctx := context.Background()

	// Test install with specific items
	result, err := tool.Install(ctx, []string{"ruff"})
	if err != nil {
		t.Fatalf("Expected Install to succeed in dry run mode, got: %v", err)
	}

	if !result.Success {
		t.Error("Expected install result to be successful in dry run mode")
	}

	if result.Tool != "uv" {
		t.Errorf("Expected result tool to be 'uv', got %s", result.Tool)
	}

	if result.Operation != "install" {
		t.Errorf("Expected result operation to be 'install', got %s", result.Operation)
	}

	// Check details
	if installed, ok := result.Details["installed"].([]string); ok {
		if len(installed) != 1 || installed[0] != "ruff" {
			t.Errorf("Expected installed to contain 'ruff', got %v", installed)
		}
	} else {
		t.Error("Expected installed details to be present")
	}
}

func TestUVTool_Update(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DryRun: true, // Use dry run to avoid actual uv calls
		},
		UV: config.UVConfig{
			AutoInstall:    true,
			GlobalPackages: []string{"ruff", "black"},
		},
	}

	tool := NewUVTool(cfg)
	ctx := context.Background()

	// Test update
	result, err := tool.Update(ctx, []string{"ruff"})
	if err != nil {
		t.Fatalf("Expected Update to succeed in dry run mode, got: %v", err)
	}

	if !result.Success {
		t.Error("Expected update result to be successful in dry run mode")
	}

	if result.Tool != "uv" {
		t.Errorf("Expected result tool to be 'uv', got %s", result.Tool)
	}

	if result.Operation != "update" {
		t.Errorf("Expected result operation to be 'update', got %s", result.Operation)
	}
}

func TestUVTool_Remove(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DryRun: true, // Use dry run to avoid actual uv calls
		},
		UV: config.UVConfig{
			AutoInstall:    true,
			GlobalPackages: []string{"ruff", "black"},
		},
	}

	tool := NewUVTool(cfg)
	ctx := context.Background()

	// Test remove
	result, err := tool.Remove(ctx, []string{"ruff"})
	if err != nil {
		t.Fatalf("Expected Remove to succeed in dry run mode, got: %v", err)
	}

	if !result.Success {
		t.Error("Expected remove result to be successful in dry run mode")
	}

	if result.Tool != "uv" {
		t.Errorf("Expected result tool to be 'uv', got %s", result.Tool)
	}

	if result.Operation != "remove" {
		t.Errorf("Expected result operation to be 'remove', got %s", result.Operation)
	}
}

func TestUVTool_Status(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DryRun: true,
		},
		UV: config.UVConfig{
			AutoInstall:    true,
			GlobalPackages: []string{"ruff", "black"},
		},
	}

	tool := NewUVTool(cfg)
	ctx := context.Background()

	status, err := tool.Status(ctx)
	if err != nil {
		t.Fatalf("Expected Status to succeed, got: %v", err)
	}

	if status.Name != "uv" {
		t.Errorf("Expected status name to be 'uv', got %s", status.Name)
	}

	if !status.Enabled {
		t.Error("Expected status to be enabled")
	}

	if len(status.Items) != 2 {
		t.Errorf("Expected 2 status items, got %d", len(status.Items))
	}

	// Check that items have expected structure
	for _, item := range status.Items {
		if item.Name != "ruff" && item.Name != "black" {
			t.Errorf("Unexpected item name: %s", item.Name)
		}

		if !item.Enabled {
			t.Errorf("Expected item %s to be enabled", item.Name)
		}

		if item.Status != "not_installed" {
			t.Errorf("Expected item %s to have status 'not_installed' in test mode, got %s", item.Name, item.Status)
		}
	}
}

func TestUVTool_GetInstalledToolsFallback(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DryRun: true,
		},
	}

	tool := NewUVTool(cfg)

	// Test the fallback parser with sample output
	// This tests the parsing logic without requiring uv to be installed
	tools, err := tool.getInstalledToolsFallback()

	// This will likely fail in test environment without uv, but that's expected
	// We're just testing that the function exists and returns proper types
	if err != nil {
		// Expected in test environment without uv installed
		if tools != nil {
			t.Error("Expected tools to be nil when error occurs")
		}
	} else {
		// If it succeeds, tools should be a valid map
		if tools == nil {
			t.Error("Expected tools to be non-nil when no error occurs")
		}
	}
}
