package theme

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/yourusername/dotfiles/test/testutil"
)

func TestNewThemeManager(t *testing.T) {
	tmpDir := testutil.TempDir(t)
	
	tm := NewThemeManager(tmpDir)
	
	if tm == nil {
		t.Fatal("Expected NewThemeManager to return a non-nil ThemeManager")
	}
	
	if tm.GetCurrentTheme() != "default" {
		t.Errorf("Expected default theme to be 'default', got %s", tm.GetCurrentTheme())
	}
}

func TestLoadThemes_WithNoFile(t *testing.T) {
	tmpDir := testutil.TempDir(t)
	tm := NewThemeManager(tmpDir)
	
	err := tm.LoadThemes()
	if err != nil {
		t.Fatalf("Expected LoadThemes to succeed when no themes file exists, got: %v", err)
	}
	
	// Should load default themes
	themes := tm.GetThemes()
	if len(themes) == 0 {
		t.Fatal("Expected default themes to be loaded")
	}
	
	// Check that default themes exist
	expectedThemes := []string{"default", "light", "cyberpunk"}
	for _, themeName := range expectedThemes {
		if _, exists := themes[themeName]; !exists {
			t.Errorf("Expected default theme %s to exist", themeName)
		}
	}
}

// createTestThemeManager creates a theme manager for testing
func createTestThemeManager(t *testing.T) (*ThemeManager, string) {
	t.Helper()
	
	tmpDir := testutil.TempDir(t)
	themeManager := NewThemeManager(tmpDir)
	
	// Create themes directory
	themesDir := filepath.Join(tmpDir, "templates")
	if err := os.MkdirAll(themesDir, 0755); err != nil {
		t.Fatalf("Failed to create themes dir: %v", err)
	}
	
	// Load default themes
	if err := themeManager.LoadThemes(); err != nil {
		t.Fatalf("Failed to load themes: %v", err)
	}
	
	return themeManager, tmpDir
}

func TestLoadThemes_WithValidFile(t *testing.T) {
	tmpDir := testutil.TempDir(t)
	tm := NewThemeManager(tmpDir)
	
	// Create themes.yaml file
	themesYAML := `themes:
  custom:
    primary: "#ff0000"
    secondary: "#00ff00"
    success: "#0000ff"
    warning: "#ffff00"
    error: "#ff00ff"
    background: "#000000"
    foreground: "#ffffff"
  another:
    primary: "#123456"
    secondary: "#654321"
    success: "#abcdef"
    warning: "#fedcba"
    error: "#111111"
    background: "#222222"
    foreground: "#333333"`
	
	testutil.CreateTestFile(t, tmpDir, "templates/themes.yaml", themesYAML)
	
	err := tm.LoadThemes()
	if err != nil {
		t.Fatalf("Expected LoadThemes to succeed with valid file, got: %v", err)
	}
	
	themes := tm.GetThemes()
	
	// Should have custom themes plus defaults
	if len(themes) < 2 {
		t.Fatalf("Expected at least 2 themes to be loaded, got %d", len(themes))
	}
	
	// Check custom theme
	custom, exists := themes["custom"]
	if !exists {
		t.Fatal("Expected custom theme to be loaded")
	}
	
	if custom.Primary != "#ff0000" {
		t.Errorf("Expected custom theme primary to be #ff0000, got %s", custom.Primary)
	}
}

func TestLoadThemes_WithInvalidFile(t *testing.T) {
	tmpDir := testutil.TempDir(t)
	tm := NewThemeManager(tmpDir)
	
	// Create invalid YAML file
	invalidYAML := `themes:
  invalid:
    primary: "#ff0000"
    - invalid syntax`
	
	testutil.CreateTestFile(t, tmpDir, "templates/themes.yaml", invalidYAML)
	
	err := tm.LoadThemes()
	if err == nil {
		t.Fatal("Expected LoadThemes to fail with invalid YAML file")
	}
}

func TestSetCurrentTheme(t *testing.T) {
	tm, _ := createTestThemeManager(t)
	
	// Test setting to existing theme
	err := tm.SetCurrentTheme("light")
	if err != nil {
		t.Fatalf("Expected SetCurrentTheme to succeed for existing theme, got: %v", err)
	}
	
	if tm.GetCurrentTheme() != "light" {
		t.Errorf("Expected current theme to be 'light', got %s", tm.GetCurrentTheme())
	}
	
	// Test setting to non-existing theme
	err = tm.SetCurrentTheme("nonexistent")
	if err == nil {
		t.Fatal("Expected SetCurrentTheme to fail for non-existing theme")
	}
}

func TestGetCurrentThemeData(t *testing.T) {
	tm, _ := createTestThemeManager(t)
	
	// Test getting default theme data
	theme := tm.GetCurrentThemeData()
	if theme.Name != "default" {
		t.Errorf("Expected theme name to be 'default', got %s", theme.Name)
	}
	
	if theme.Primary == "" {
		t.Error("Expected theme to have a primary color")
	}
	
	// Test getting theme data after switching
	tm.SetCurrentTheme("light")
	theme = tm.GetCurrentThemeData()
	if theme.Name != "light" {
		t.Errorf("Expected theme name to be 'light', got %s", theme.Name)
	}
}

func TestGetStyles(t *testing.T) {
	tm, _ := createTestThemeManager(t)
	
	styles := tm.GetStyles()
	if styles == nil {
		t.Fatal("Expected GetStyles to return non-nil styles")
	}
	
	// Test that styles are cached
	styles2 := tm.GetStyles()
	if styles != styles2 {
		t.Error("Expected styles to be cached and return same instance")
	}
	
	// Test that cache is cleared when theme changes
	tm.SetCurrentTheme("light")
	styles3 := tm.GetStyles()
	if styles == styles3 {
		t.Error("Expected styles to be regenerated after theme change")
	}
}

func TestAddTheme(t *testing.T) {
	tm, _ := createTestThemeManager(t)
	
	initialCount := len(tm.GetThemes())
	
	newTheme := Theme{
		Primary:    "#ff0000",
		Secondary:  "#00ff00",
		Success:    "#0000ff",
		Warning:    "#ffff00",
		Error:      "#ff00ff",
		Background: "#000000",
		Foreground: "#ffffff",
	}
	
	tm.AddTheme("custom", newTheme)
	
	themes := tm.GetThemes()
	if len(themes) != initialCount+1 {
		t.Errorf("Expected %d themes after adding, got %d", initialCount+1, len(themes))
	}
	
	added, exists := themes["custom"]
	if !exists {
		t.Fatal("Expected custom theme to exist after adding")
	}
	
	if added.Name != "custom" {
		t.Errorf("Expected theme name to be 'custom', got %s", added.Name)
	}
	
	if added.Primary != "#ff0000" {
		t.Errorf("Expected theme primary to be #ff0000, got %s", added.Primary)
	}
}

func TestRemoveTheme(t *testing.T) {
	tm, _ := createTestThemeManager(t)
	
	// Add a custom theme first
	customTheme := Theme{
		Primary:    "#ff0000",
		Secondary:  "#00ff00",
		Success:    "#0000ff",
		Warning:    "#ffff00",
		Error:      "#ff00ff",
		Background: "#000000",
		Foreground: "#ffffff",
	}
	tm.AddTheme("custom", customTheme)
	
	// Test removing custom theme
	err := tm.RemoveTheme("custom")
	if err != nil {
		t.Fatalf("Expected RemoveTheme to succeed for custom theme, got: %v", err)
	}
	
	themes := tm.GetThemes()
	if _, exists := themes["custom"]; exists {
		t.Error("Expected custom theme to be removed")
	}
	
	// Test removing built-in theme (should fail)
	err = tm.RemoveTheme("default")
	if err == nil {
		t.Fatal("Expected RemoveTheme to fail for built-in theme")
	}
	
	// Test removing non-existent theme
	err = tm.RemoveTheme("nonexistent")
	if err == nil {
		t.Fatal("Expected RemoveTheme to fail for non-existent theme")
	}
}

func TestRemoveTheme_CurrentTheme(t *testing.T) {
	tm, _ := createTestThemeManager(t)
	
	// Add and switch to custom theme
	customTheme := Theme{
		Primary:    "#ff0000",
		Secondary:  "#00ff00",
		Success:    "#0000ff",
		Warning:    "#ffff00",
		Error:      "#ff00ff",
		Background: "#000000",
		Foreground: "#ffffff",
	}
	tm.AddTheme("custom", customTheme)
	tm.SetCurrentTheme("custom")
	
	// Remove current theme
	err := tm.RemoveTheme("custom")
	if err != nil {
		t.Fatalf("Expected RemoveTheme to succeed, got: %v", err)
	}
	
	// Should switch back to default
	if tm.GetCurrentTheme() != "default" {
		t.Errorf("Expected current theme to be 'default' after removing current theme, got %s", tm.GetCurrentTheme())
	}
}

func TestSaveThemes(t *testing.T) {
	tm, tmpDir := createTestThemeManager(t)
	
	// Add a custom theme
	customTheme := Theme{
		Primary:    "#ff0000",
		Secondary:  "#00ff00",
		Success:    "#0000ff",
		Warning:    "#ffff00",
		Error:      "#ff00ff",
		Background: "#000000",
		Foreground: "#ffffff",
	}
	tm.AddTheme("custom", customTheme)
	
	// Save themes
	err := tm.SaveThemes()
	if err != nil {
		t.Fatalf("Expected SaveThemes to succeed, got: %v", err)
	}
	
	// Check that file was created
	themesPath := filepath.Join(tmpDir, "templates", "themes.yaml")
	testutil.AssertFileExists(t, themesPath)
	
	// Check that file contains custom theme
	testutil.AssertFileContains(t, themesPath, "custom:")
	testutil.AssertFileContains(t, themesPath, "#ff0000")
}

func TestCreateThemeFromCurrent(t *testing.T) {
	tm, _ := createTestThemeManager(t)
	
	// Switch to light theme
	tm.SetCurrentTheme("light")
	
	// Create theme from current
	newTheme := tm.CreateThemeFromCurrent("my-light")
	
	if newTheme.Name != "my-light" {
		t.Errorf("Expected new theme name to be 'my-light', got %s", newTheme.Name)
	}
	
	// Should have same colors as light theme
	lightTheme := tm.GetCurrentThemeData()
	if newTheme.Primary != lightTheme.Primary {
		t.Errorf("Expected new theme primary to match light theme, got %s vs %s", newTheme.Primary, lightTheme.Primary)
	}
}

func TestGetThemeNames(t *testing.T) {
	tm, _ := createTestThemeManager(t)
	
	names := tm.GetThemeNames()
	if len(names) == 0 {
		t.Fatal("Expected theme names to be returned")
	}
	
	// Should contain default themes
	expectedThemes := []string{"default", "light", "cyberpunk"}
	for _, expected := range expectedThemes {
		found := false
		for _, name := range names {
			if name == expected {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected theme names to contain %s", expected)
		}
	}
}

func TestThemeValidation(t *testing.T) {
	tm, tmpDir := createTestThemeManager(t)
	
	// Test with missing required fields
	incompleteYAML := `themes:
  incomplete:
    primary: "#ff0000"
    # missing other required fields`
	
	testutil.CreateTestFile(t, tmpDir, "templates/themes.yaml", incompleteYAML)
	
	// Load themes - should still work but theme may have empty fields
	err := tm.LoadThemes()
	if err != nil {
		t.Fatalf("Expected LoadThemes to handle incomplete theme, got: %v", err)
	}
	
	theme, exists := tm.GetTheme("incomplete")
	if !exists {
		t.Fatal("Expected incomplete theme to be loaded")
	}
	
	if theme.Primary != "#ff0000" {
		t.Errorf("Expected primary color to be preserved, got %s", theme.Primary)
	}
}