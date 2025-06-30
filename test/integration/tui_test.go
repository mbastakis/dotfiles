package integration

import (
	"context"
	"testing"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/theme"
	"github.com/mbastakis/dotfiles/internal/tools"
	"github.com/mbastakis/dotfiles/internal/tui/models"
	"github.com/mbastakis/dotfiles/internal/tui/screens"
	"github.com/mbastakis/dotfiles/internal/types"
	"github.com/mbastakis/dotfiles/test/testutil"
)

// TestTUIIntegration tests the overall TUI integration
func TestTUIIntegration(t *testing.T) {
	// Create test configuration
	tmpDir := testutil.TempDir(t)
	cfg := createTestConfig(tmpDir)
	
	// Create theme manager
	themeManager := theme.NewThemeManager(tmpDir)
	themeManager.LoadThemes()
	
	// Create tool registry with mock tools
	registry := tools.NewToolRegistry()
	mockTool := &MockTool{name: "test-tool", enabled: true, priority: 1}
	registry.Register(mockTool)
	
	// Create app model
	appModel := models.NewAppModel(cfg, registry, themeManager)
	
	// Test initialization
	cmd := appModel.Init()
	if cmd == nil {
		t.Error("Expected Init to return a command")
	}
	
	// Test window size update
	newModel, _ := appModel.Update(tea.WindowSizeMsg{Width: 80, Height: 24})
	appModel = newModel.(models.AppModel)
	
	// Test view rendering
	view := appModel.View()
	if view == "" {
		t.Error("Expected View to return non-empty string")
	}
	
	// Should contain main menu elements
	if !contains(view, "Dotfiles Manager") {
		t.Error("Expected view to contain main title")
	}
}

func TestThemesScreenIntegration(t *testing.T) {
	// Create test configuration
	tmpDir := testutil.TempDir(t)
	cfg := createTestConfig(tmpDir)
	
	// Create theme manager
	themeManager := theme.NewThemeManager(tmpDir)
	themeManager.LoadThemes()
	
	// Create themes screen
	themesScreen := screens.NewThemesScreen(cfg, themeManager, 80, 24)
	
	// Test initialization
	cmd := themesScreen.Init()
	if cmd != nil {
		t.Error("Expected themes screen Init to return nil")
	}
	
	// Test view rendering
	view := themesScreen.View()
	if view == "" {
		t.Error("Expected themes screen View to return non-empty string")
	}
	
	// Should contain themes screen elements
	if !contains(view, "Theme Selection") {
		t.Error("Expected view to contain theme selection title")
	}
	
	// Should contain default themes
	if !contains(view, "Default") {
		t.Error("Expected view to contain Default theme")
	}
}

func TestOverviewScreenIntegration(t *testing.T) {
	// Create test configuration
	tmpDir := testutil.TempDir(t)
	cfg := createTestConfig(tmpDir)
	
	// Create theme manager
	themeManager := theme.NewThemeManager(tmpDir)
	themeManager.LoadThemes()
	
	// Create tool registry with mock tools
	registry := tools.NewToolRegistry()
	mockTool := &MockTool{name: "test-tool", enabled: true, priority: 1}
	registry.Register(mockTool)
	
	// Create overview screen
	overviewScreen := screens.NewOverviewScreen(cfg, registry, themeManager, 80, 24)
	
	// Test initialization
	cmd := overviewScreen.Init()
	if cmd == nil {
		t.Error("Expected overview screen Init to return a command")
	}
	
	// Test view rendering (may show loading initially)
	view := overviewScreen.View()
	if view == "" {
		t.Error("Expected overview screen View to return non-empty string")
	}
	
	// Should contain overview screen elements
	if !contains(view, "System Overview") {
		t.Error("Expected view to contain system overview title")
	}
}

func TestSettingsScreenIntegration(t *testing.T) {
	// Create test configuration
	tmpDir := testutil.TempDir(t)
	cfg := createTestConfig(tmpDir)
	
	// Create theme manager
	themeManager := theme.NewThemeManager(tmpDir)
	themeManager.LoadThemes()
	
	// Create settings screen
	settingsScreen := screens.NewSettingsScreen(cfg, themeManager, 80, 24)
	
	// Test initialization
	cmd := settingsScreen.Init()
	if cmd != nil {
		t.Error("Expected settings screen Init to return nil")
	}
	
	// Test view rendering
	view := settingsScreen.View()
	if view == "" {
		t.Error("Expected settings screen View to return non-empty string")
	}
	
	// Should contain settings screen elements
	if !contains(view, "Configuration Settings") {
		t.Error("Expected view to contain configuration settings title")
	}
	
	// Should contain some settings
	if !contains(view, "Log Level") {
		t.Error("Expected view to contain Log Level setting")
	}
}

func TestToolScreenIntegration(t *testing.T) {
	// Create test configuration
	tmpDir := testutil.TempDir(t)
	themeManager := theme.NewThemeManager(tmpDir)
	themeManager.LoadThemes()
	
	// Create mock tool
	mockTool := &MockTool{name: "test-tool", enabled: true, priority: 1}
	
	// Create tool screen
	toolScreen := screens.NewToolScreen(mockTool, themeManager, 80, 24)
	
	// Test initialization
	cmd := toolScreen.Init()
	if cmd == nil {
		t.Error("Expected tool screen Init to return a command")
	}
	
	// Test view rendering (may show loading initially)
	view := toolScreen.View()
	if view == "" {
		t.Error("Expected tool screen View to return non-empty string")
	}
	
	// Should contain tool screen elements
	if !contains(view, "Tool Management") {
		t.Error("Expected view to contain tool management title")
	}
}

func TestThemeManagerIntegration(t *testing.T) {
	tmpDir := testutil.TempDir(t)
	
	// Create theme manager
	themeManager := theme.NewThemeManager(tmpDir)
	err := themeManager.LoadThemes()
	if err != nil {
		t.Fatalf("Failed to load themes: %v", err)
	}
	
	// Test theme switching
	originalTheme := themeManager.GetCurrentTheme()
	
	err = themeManager.SetCurrentTheme("light")
	if err != nil {
		t.Fatalf("Failed to set theme: %v", err)
	}
	
	if themeManager.GetCurrentTheme() != "light" {
		t.Errorf("Expected current theme to be 'light', got %s", themeManager.GetCurrentTheme())
	}
	
	// Test style generation
	styles := themeManager.GetStyles()
	if styles == nil {
		t.Fatal("Expected styles to be generated")
	}
	
	// Switch back and verify styles change
	err = themeManager.SetCurrentTheme(originalTheme)
	if err != nil {
		t.Fatalf("Failed to reset theme: %v", err)
	}
	
	newStyles := themeManager.GetStyles()
	if styles == newStyles {
		t.Error("Expected styles to change when theme changes")
	}
}

// Helper functions

func createTestConfig(tmpDir string) *config.Config {
	return &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath:   tmpDir,
			LogLevel:       "info",
			DryRun:         false,
			AutoConfirm:    false,
			BackupEnabled:  true,
			BackupSuffix:   ".backup",
		},
		TUI: config.TUIConfig{
			ColorScheme:        "default",
			Animations:         true,
			ConfirmDestructive: true,
			ShowProgress:       true,
		},
		Stow: config.StowConfig{
			Packages: []config.StowPackage{
				{Name: "test", Target: tmpDir + "/home", Enabled: true, Priority: 1},
			},
		},
	}
}

// MockTool for integration testing
type MockTool struct {
	name     string
	enabled  bool
	priority int
}

func (m *MockTool) Name() string {
	return m.name
}

func (m *MockTool) IsEnabled() bool {
	return m.enabled
}

func (m *MockTool) Priority() int {
	return m.priority
}

func (m *MockTool) Validate() error {
	return nil
}

func (m *MockTool) Status(ctx context.Context) (*types.ToolStatus, error) {
	return &types.ToolStatus{
		Name:    m.name,
		Enabled: m.enabled,
		Healthy: true,
		Items: []types.ToolItem{
			{Name: "test-item", Enabled: true, Installed: true},
		},
	}, nil
}

func (m *MockTool) Install(ctx context.Context, items []string) (*types.OperationResult, error) {
	return &types.OperationResult{
		Tool:      m.name,
		Operation: "install",
		Success:   true,
		Message:   "Install completed",
	}, nil
}

func (m *MockTool) Update(ctx context.Context, items []string) (*types.OperationResult, error) {
	return &types.OperationResult{
		Tool:      m.name,
		Operation: "update",
		Success:   true,
		Message:   "Update completed",
	}, nil
}

func (m *MockTool) Remove(ctx context.Context, items []string) (*types.OperationResult, error) {
	return &types.OperationResult{
		Tool:      m.name,
		Operation: "remove",
		Success:   true,
		Message:   "Remove completed",
	}, nil
}

func (m *MockTool) List(ctx context.Context) ([]types.ToolItem, error) {
	return []types.ToolItem{
		{Name: "test-item", Enabled: true, Installed: true},
	}, nil
}

func (m *MockTool) Sync(ctx context.Context) (*types.OperationResult, error) {
	return &types.OperationResult{
		Tool:      m.name,
		Operation: "sync",
		Success:   true,
		Message:   "Sync completed",
	}, nil
}

func (m *MockTool) Configure(config interface{}) error {
	return nil
}

// Helper function for string contains check
func contains(s, substr string) bool {
	return len(s) >= len(substr) && containsHelper(s, substr)
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}