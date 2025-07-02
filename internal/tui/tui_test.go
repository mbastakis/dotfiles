package tui

import (
	"testing"

	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/tools"
)

func TestNewTUI(t *testing.T) {
	// Create test config
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		TUI: config.TUIConfig{
			ColorScheme: "default",
		},
	}

	// Create test registry
	registry := tools.NewToolRegistry()

	// Create TUI instance
	tui := NewTUI(cfg, registry)

	if tui == nil {
		t.Fatal("Expected NewTUI to return non-nil instance")
	}

	if tui.config != cfg {
		t.Error("Expected TUI config to match provided config")
	}

	if tui.registry != registry {
		t.Error("Expected TUI registry to match provided registry")
	}

	if tui.themeManager == nil {
		t.Error("Expected TUI to have a theme manager")
	}
}

func TestNewTUI_WithCustomTheme(t *testing.T) {
	// Create test config with custom theme
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		TUI: config.TUIConfig{
			ColorScheme: "dark",
		},
	}

	registry := tools.NewToolRegistry()
	tui := NewTUI(cfg, registry)

	if tui == nil {
		t.Fatal("Expected NewTUI to return non-nil instance")
	}

	// Theme manager should be initialized even with custom theme
	if tui.themeManager == nil {
		t.Error("Expected TUI to have a theme manager")
	}
}

func TestNewTUI_WithEmptyTheme(t *testing.T) {
	// Create test config with empty theme
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		TUI: config.TUIConfig{
			ColorScheme: "",
		},
	}

	registry := tools.NewToolRegistry()
	tui := NewTUI(cfg, registry)

	if tui == nil {
		t.Fatal("Expected NewTUI to return non-nil instance")
	}

	// Theme manager should still be initialized
	if tui.themeManager == nil {
		t.Error("Expected TUI to have a theme manager")
	}
}

func TestTUI_Fields(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		TUI: config.TUIConfig{
			ColorScheme: "default",
		},
	}

	registry := tools.NewToolRegistry()
	tui := NewTUI(cfg, registry)

	// Test that all fields are properly set
	if tui.config == nil {
		t.Error("Expected config field to be set")
	}

	if tui.registry == nil {
		t.Error("Expected registry field to be set")
	}

	if tui.themeManager == nil {
		t.Error("Expected themeManager field to be set")
	}

	// Program should be nil until Run() is called
	if tui.program != nil {
		t.Error("Expected program field to be nil before Run()")
	}
}
