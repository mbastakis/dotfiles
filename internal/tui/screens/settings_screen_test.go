package screens

import (
	"testing"

	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/theme"
)

func TestSettingItem(t *testing.T) {
	item := SettingItem{
		key:         "test.setting",
		name:        "Test Setting",
		description: "A test setting description",
		value:       "test_value",
		settingType: StringSetting,
		options:     []string{},
	}

	if item.Title() != "Test Setting" {
		t.Errorf("Expected title to be 'Test Setting', got '%s'", item.Title())
	}

	if item.FilterValue() != "Test Setting" {
		t.Errorf("Expected filter value to be 'Test Setting', got '%s'", item.FilterValue())
	}

	if item.Description() != "A test setting description (Current: test_value)" {
		t.Errorf("Expected description to include current value, got '%s'", item.Description())
	}
}

func TestSettingTypes(t *testing.T) {
	tests := []struct {
		name        string
		settingType SettingType
		expected    int
	}{
		{"StringSetting", StringSetting, 0},
		{"BoolSetting", BoolSetting, 1},
		{"IntSetting", IntSetting, 2},
		{"EnumSetting", EnumSetting, 3},
		{"PathSetting", PathSetting, 4},
	}

	for _, test := range tests {
		if int(test.settingType) != test.expected {
			t.Errorf("Expected %s to have value %d, got %d", test.name, test.expected, int(test.settingType))
		}
	}
}

func TestNewSettingsScreen(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{
			DotfilesPath: "/test/path",
			DryRun:       false,
		},
		TUI: config.TUIConfig{
			ColorScheme: "default",
		},
	}

	themeManager := theme.NewThemeManager("/test/path")

	screen := NewSettingsScreen(cfg, themeManager, 80, 24)

	if screen.config != cfg {
		t.Error("Expected screen config to match provided config")
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

	if screen.editMode {
		t.Error("Expected screen to not be in edit mode initially")
	}

	if screen.currentSetting != nil {
		t.Error("Expected currentSetting to be nil initially")
	}
}

func TestSettingsScreen_Dimensions(t *testing.T) {
	cfg := &config.Config{
		Global: config.GlobalConfig{DotfilesPath: "/test"},
		TUI:    config.TUIConfig{ColorScheme: "default"},
	}

	themeManager := theme.NewThemeManager("/test")

	screen := NewSettingsScreen(cfg, themeManager, 100, 50)

	if screen.width != 100 {
		t.Errorf("Expected width to be 100, got %d", screen.width)
	}

	if screen.height != 50 {
		t.Errorf("Expected height to be 50, got %d", screen.height)
	}
}

func TestSettingItem_WithOptions(t *testing.T) {
	item := SettingItem{
		key:         "theme.color",
		name:        "Color Scheme",
		description: "UI color scheme",
		value:       "dark",
		settingType: EnumSetting,
		options:     []string{"light", "dark", "auto"},
	}

	if len(item.options) != 3 {
		t.Errorf("Expected 3 options, got %d", len(item.options))
	}

	expectedOptions := []string{"light", "dark", "auto"}
	for i, expected := range expectedOptions {
		if item.options[i] != expected {
			t.Errorf("Expected option %d to be '%s', got '%s'", i, expected, item.options[i])
		}
	}
}

func TestSettingItem_BooleanSetting(t *testing.T) {
	item := SettingItem{
		key:         "global.dryrun",
		name:        "Dry Run Mode",
		description: "Enable dry run mode",
		value:       "true",
		settingType: BoolSetting,
		options:     []string{},
	}

	if item.settingType != BoolSetting {
		t.Errorf("Expected setting type to be BoolSetting, got %v", item.settingType)
	}

	if item.value != "true" {
		t.Errorf("Expected value to be 'true', got '%s'", item.value)
	}
}

func TestSettingItem_PathSetting(t *testing.T) {
	item := SettingItem{
		key:         "global.dotfiles_path",
		name:        "Dotfiles Path",
		description: "Path to dotfiles directory",
		value:       "/home/user/dotfiles",
		settingType: PathSetting,
		options:     []string{},
	}

	if item.settingType != PathSetting {
		t.Errorf("Expected setting type to be PathSetting, got %v", item.settingType)
	}

	if item.value != "/home/user/dotfiles" {
		t.Errorf("Expected value to be '/home/user/dotfiles', got '%s'", item.value)
	}
}
