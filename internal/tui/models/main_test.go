package models

import (
	"testing"

	"github.com/charmbracelet/bubbles/key"
	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/theme"
	"github.com/mbastakis/dotfiles/internal/tools"
)

func TestMenuItem(t *testing.T) {
	item := MenuItem{
		title:       "Test Tool",
		description: "A test tool description",
		tool:        nil, // Mock tool
	}
	
	if item.Title() != "Test Tool" {
		t.Errorf("Expected title to be 'Test Tool', got '%s'", item.Title())
	}
	
	if item.Description() != "A test tool description" {
		t.Errorf("Expected description to be 'A test tool description', got '%s'", item.Description())
	}
	
	if item.FilterValue() != "Test Tool" {
		t.Errorf("Expected filter value to be 'Test Tool', got '%s'", item.FilterValue())
	}
}

func TestNewMainModel(t *testing.T) {
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
	
	model := NewMainModel(cfg, registry, themeManager)
	
	// NewMainModel returns a struct value, not a pointer, so it's always non-nil
	// We'll just verify the fields are set correctly
	
	if model.config != cfg {
		t.Error("Expected model config to match provided config")
	}
	
	if model.registry != registry {
		t.Error("Expected model registry to match provided registry")
	}
	
	if model.themeManager != themeManager {
		t.Error("Expected model themeManager to match provided themeManager")
	}
	
	if model.ready {
		t.Error("Expected model to not be ready initially")
	}
}

func TestKeyMapShortHelp(t *testing.T) {
	keymap := keyMap{
		Enter:  createTestBinding("enter", "select"),
		Status: createTestBinding("s", "status"),
		Quit:   createTestBinding("q", "quit"),
		Help:   createTestBinding("?", "help"),
	}
	
	shortHelp := keymap.ShortHelp()
	
	expectedLength := 4
	if len(shortHelp) != expectedLength {
		t.Errorf("Expected ShortHelp to return %d bindings, got %d", expectedLength, len(shortHelp))
	}
}

func TestKeyMapFullHelp(t *testing.T) {
	keymap := keyMap{
		Up:     createTestBinding("up", "move up"),
		Down:   createTestBinding("down", "move down"),
		Enter:  createTestBinding("enter", "select"),
		Status: createTestBinding("s", "status"),
		Quit:   createTestBinding("q", "quit"),
		Help:   createTestBinding("?", "help"),
	}
	
	fullHelp := keymap.FullHelp()
	
	if len(fullHelp) == 0 {
		t.Error("Expected FullHelp to return non-empty slice")
	}
	
	// Check that we have grouped bindings
	totalBindings := 0
	for _, group := range fullHelp {
		totalBindings += len(group)
	}
	
	if totalBindings == 0 {
		t.Error("Expected FullHelp to contain bindings")
	}
}

func TestMainModel_Dimensions(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{DotfilesPath: "/test"},
		TUI:    config.TUIConfig{ColorScheme: "default"},
	}
	
	registry := tools.NewToolRegistry()
	themeManager := theme.NewThemeManager("/test")
	
	model := NewMainModel(cfg, registry, themeManager)
	
	// Test initial dimensions
	if model.width != 0 {
		t.Errorf("Expected initial width to be 0, got %d", model.width)
	}
	
	if model.height != 0 {
		t.Errorf("Expected initial height to be 0, got %d", model.height)
	}
}

// Helper function to create test key bindings
func createTestBinding(keyName, help string) key.Binding {
	return key.NewBinding(
		key.WithKeys(keyName),
		key.WithHelp(keyName, help),
	)
}