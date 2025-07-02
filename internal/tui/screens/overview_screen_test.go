package screens

import (
	"testing"

	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/theme"
	"github.com/mbastakis/dotfiles/internal/tools"
	"github.com/mbastakis/dotfiles/internal/types"
)

func TestNewOverviewScreen(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
		},
		TUI: config.TUIConfig{
			ColorScheme: "default",
		},
	}

	registry := tools.NewToolRegistry()
	themeManager := theme.NewThemeManager("/test/path")

	screen := NewOverviewScreen(cfg, registry, themeManager, 80, 24)

	if screen.config != cfg {
		t.Error("Expected screen config to match provided config")
	}

	if screen.registry != registry {
		t.Error("Expected screen registry to match provided registry")
	}

	if screen.themeManager != themeManager {
		t.Error("Expected screen themeManager to match provided themeManager")
	}

	if screen.width != 80 {
		t.Errorf("Expected width to be 80, got %d", screen.width)
	}

	if screen.height != 24 {
		t.Errorf("Expected height to be 24, got %d", screen.height)
	}

	if screen.loading {
		t.Error("Expected screen to not be loading initially")
	}

	if screen.statuses == nil {
		t.Error("Expected statuses map to be initialized")
	}
}

func TestSystemStatusMsg(t *testing.T) {
	msg := SystemStatusMsg{
		Statuses: map[string]*types.ToolStatus{},
		Error:    nil,
	}

	if msg.Statuses == nil {
		t.Error("Expected Statuses to be initialized")
	}

	if msg.Error != nil {
		t.Error("Expected Error to be nil")
	}
}

func TestOverviewScreen_Dimensions(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{DotfilesPath: "/test"},
		TUI:    config.TUIConfig{ColorScheme: "default"},
	}

	registry := tools.NewToolRegistry()
	themeManager := theme.NewThemeManager("/test")

	screen := NewOverviewScreen(cfg, registry, themeManager, 100, 50)

	if screen.width != 100 {
		t.Errorf("Expected width to be 100, got %d", screen.width)
	}

	if screen.height != 50 {
		t.Errorf("Expected height to be 50, got %d", screen.height)
	}
}

func TestFormatBytes(t *testing.T) {
	tests := []struct {
		input    uint64
		expected string
	}{
		{0, "0 B"},
		{100, "100 B"},
		{1024, "1.0 KB"},
		{1536, "1.5 KB"},
		{1048576, "1.0 MB"},
		{1073741824, "1.0 GB"},
	}

	for _, test := range tests {
		result := formatBytes(test.input)
		if result != test.expected {
			t.Errorf("formatBytes(%d) = %s, expected %s", test.input, result, test.expected)
		}
	}
}

func TestOverviewScreen_ViewBasic(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{DotfilesPath: "/test"},
		TUI:    config.TUIConfig{ColorScheme: "default"},
	}

	registry := tools.NewToolRegistry()
	themeManager := theme.NewThemeManager("/test")

	screen := NewOverviewScreen(cfg, registry, themeManager, 80, 24)

	// Test view when screen is not initialized (width/height = 0)
	screen.width = 0
	screen.height = 0
	view := screen.View()
	if view != "Initializing overview screen..." {
		t.Errorf("Expected initialization message, got: %s", view)
	}

	// Test loading view
	screen.width = 80
	screen.height = 24
	screen.loading = true
	view = screen.View()
	if len(view) == 0 {
		t.Error("Expected loading view to return non-empty string")
	}
}
