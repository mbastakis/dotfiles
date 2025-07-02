package npm

import (
	"context"
	"testing"

	"github.com/mbastakis/dotfiles/internal/config"
)

func TestNewNPMTool(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
			DryRun:       false,
		},
		NPM: config.NPMConfig{
			AutoInstall:    true,
			AutoUpdate:     true,
			GlobalPackages: []string{"@anthropic-ai/claude-code", "typescript"},
		},
	}

	tool := NewNPMTool(cfg)

	if tool == nil {
		t.Fatal("Expected NewNPMTool to return non-nil tool")
	}

	if tool.Name() != "npm" {
		t.Errorf("Expected tool name to be 'npm', got %s", tool.Name())
	}

	if tool.Priority() != 50 {
		t.Errorf("Expected priority to be 50, got %d", tool.Priority())
	}

	if !tool.IsEnabled() {
		t.Error("Expected tool to be enabled")
	}
}

func TestNPMTool_List(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DryRun: true, // Use dry run to avoid actual npm calls
		},
		NPM: config.NPMConfig{
			AutoInstall:    true,
			AutoUpdate:     true,
			GlobalPackages: []string{"typescript", "eslint", "prettier"},
		},
	}

	tool := NewNPMTool(cfg)
	ctx := context.Background()

	items, err := tool.List(ctx)
	if err != nil {
		t.Fatalf("Expected List to succeed, got: %v", err)
	}

	if len(items) != 3 {
		t.Errorf("Expected 3 items, got %d", len(items))
	}

	expectedPackages := map[string]bool{
		"typescript": true,
		"eslint":     true,
		"prettier":   true,
	}

	for _, item := range items {
		if !expectedPackages[item.Name] {
			t.Errorf("Unexpected package in list: %s", item.Name)
		}

		if !item.Enabled {
			t.Errorf("Expected package %s to be enabled", item.Name)
		}
	}
}

func TestNPMTool_Configure(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		NPM: config.NPMConfig{
			AutoInstall:    true,
			GlobalPackages: []string{"typescript"},
		},
	}

	tool := NewNPMTool(cfg)

	// Test with valid config
	newConfig := &config.NPMConfig{
		AutoInstall:    false,
		AutoUpdate:     true,
		GlobalPackages: []string{"eslint", "prettier"},
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

func TestNPMTool_Sync(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DryRun: true, // Use dry run to avoid actual npm calls
		},
		NPM: config.NPMConfig{
			AutoInstall:    true,
			AutoUpdate:     false,
			GlobalPackages: []string{"typescript", "eslint"},
		},
	}

	tool := NewNPMTool(cfg)
	ctx := context.Background()

	// Test sync operation
	result, err := tool.Sync(ctx)
	if err != nil {
		t.Fatalf("Expected Sync to succeed in dry run mode, got: %v", err)
	}

	if !result.Success {
		t.Error("Expected sync result to be successful in dry run mode")
	}

	if result.Tool != "npm" {
		t.Errorf("Expected result tool to be 'npm', got %s", result.Tool)
	}

	// Sync operation may map to install for NPM
	if result.Operation != "sync" && result.Operation != "install" {
		t.Errorf("Expected result operation to be 'sync' or 'install', got %s", result.Operation)
	}
}
