package theme

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/charmbracelet/lipgloss"
	"gopkg.in/yaml.v3"
)

// Theme represents a color theme for the TUI
type Theme struct {
	Name       string `yaml:"-"`
	Primary    string `yaml:"primary"`
	Secondary  string `yaml:"secondary"`
	Success    string `yaml:"success"`
	Warning    string `yaml:"warning"`
	Error      string `yaml:"error"`
	Background string `yaml:"background"`
	Foreground string `yaml:"foreground"`
}

// ThemeConfig represents the themes configuration file
type ThemeConfig struct {
	Themes map[string]Theme `yaml:"themes"`
}

// ThemeManager manages theme loading and application
type ThemeManager struct {
	themes       map[string]Theme
	currentTheme string
	dotfilesPath string
	cachedStyles *Styles
}

// Styles contains pre-computed lipgloss styles for the current theme
type Styles struct {
	// Common UI styles
	Title    lipgloss.Style
	Subtitle lipgloss.Style
	Header   lipgloss.Style
	Footer   lipgloss.Style
	Help     lipgloss.Style
	Error    lipgloss.Style
	Success  lipgloss.Style
	Warning  lipgloss.Style
	Info     lipgloss.Style

	// Layout styles
	Box          lipgloss.Style
	ActiveBox    lipgloss.Style
	Border       lipgloss.Style
	ActiveBorder lipgloss.Style

	// Interactive element styles
	Button       lipgloss.Style
	ActiveButton lipgloss.Style
	Input        lipgloss.Style
	InputFocus   lipgloss.Style

	// Status indicator styles
	Healthy   lipgloss.Style
	Unhealthy lipgloss.Style
	Disabled  lipgloss.Style
	Pending   lipgloss.Style
}

// NewThemeManager creates a new theme manager
func NewThemeManager(dotfilesPath string) *ThemeManager {
	return &ThemeManager{
		themes:       make(map[string]Theme),
		currentTheme: "default",
		dotfilesPath: dotfilesPath,
	}
}

// LoadThemes loads themes from the themes.yaml file
func (tm *ThemeManager) LoadThemes() error {
	themesPath := filepath.Join(tm.dotfilesPath, "templates", "themes.yaml")

	// Check if themes file exists
	if _, err := os.Stat(themesPath); os.IsNotExist(err) {
		// Load default themes if file doesn't exist
		tm.loadDefaultThemes()
		return nil
	}

	// Read themes file
	data, err := os.ReadFile(themesPath)
	if err != nil {
		return fmt.Errorf("failed to read themes file: %w", err)
	}

	// Parse YAML
	var config ThemeConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return fmt.Errorf("failed to parse themes file: %w", err)
	}

	// Store themes with names
	for name, theme := range config.Themes {
		theme.Name = name
		tm.themes[name] = theme
	}

	// Load default themes if none were found
	if len(tm.themes) == 0 {
		tm.loadDefaultThemes()
	}

	return nil
}

// loadDefaultThemes loads built-in default themes
func (tm *ThemeManager) loadDefaultThemes() {
	tm.themes["default"] = Theme{
		Name:       "default",
		Primary:    "#25A065",
		Secondary:  "#00d7ff",
		Success:    "#00ff00",
		Warning:    "#ffaa00",
		Error:      "#ff0000",
		Background: "#1e1e1e",
		Foreground: "#ffffff",
	}

	tm.themes["light"] = Theme{
		Name:       "light",
		Primary:    "#0066cc",
		Secondary:  "#0099cc",
		Success:    "#008800",
		Warning:    "#cc6600",
		Error:      "#cc0000",
		Background: "#ffffff",
		Foreground: "#000000",
	}

	tm.themes["cyberpunk"] = Theme{
		Name:       "cyberpunk",
		Primary:    "#ff007f",
		Secondary:  "#00ffff",
		Success:    "#00ff41",
		Warning:    "#ffaa00",
		Error:      "#ff073a",
		Background: "#0d1117",
		Foreground: "#00ff41",
	}
}

// GetTheme returns a theme by name
func (tm *ThemeManager) GetTheme(name string) (Theme, bool) {
	theme, exists := tm.themes[name]
	return theme, exists
}

// GetThemes returns all available themes
func (tm *ThemeManager) GetThemes() map[string]Theme {
	return tm.themes
}

// GetThemeNames returns all theme names
func (tm *ThemeManager) GetThemeNames() []string {
	names := make([]string, 0, len(tm.themes))
	for name := range tm.themes {
		names = append(names, name)
	}
	return names
}

// SetCurrentTheme sets the active theme and regenerates styles
func (tm *ThemeManager) SetCurrentTheme(name string) error {
	if _, exists := tm.themes[name]; !exists {
		return fmt.Errorf("theme '%s' not found", name)
	}

	tm.currentTheme = name
	tm.cachedStyles = nil // Clear cache to force regeneration
	return nil
}

// GetCurrentTheme returns the current theme name
func (tm *ThemeManager) GetCurrentTheme() string {
	return tm.currentTheme
}

// GetCurrentThemeData returns the current theme data
func (tm *ThemeManager) GetCurrentThemeData() Theme {
	if theme, exists := tm.themes[tm.currentTheme]; exists {
		return theme
	}
	// Return default theme if current theme is not found
	return tm.themes["default"]
}

// GetStyles returns the cached styles for the current theme
func (tm *ThemeManager) GetStyles() *Styles {
	if tm.cachedStyles == nil {
		tm.generateStyles()
	}
	return tm.cachedStyles
}

// generateStyles creates lipgloss styles based on the current theme
func (tm *ThemeManager) generateStyles() {
	theme := tm.GetCurrentThemeData()

	// Base colors
	primary := lipgloss.Color(theme.Primary)
	secondary := lipgloss.Color(theme.Secondary)
	success := lipgloss.Color(theme.Success)
	warning := lipgloss.Color(theme.Warning)
	errorColor := lipgloss.Color(theme.Error)
	foreground := lipgloss.Color(theme.Foreground)
	background := lipgloss.Color(theme.Background)

	// Derived colors
	dimmed := lipgloss.Color("#626262")
	border := lipgloss.Color("#404040")
	activeBorder := primary

	tm.cachedStyles = &Styles{
		// Common UI styles
		Title: lipgloss.NewStyle().
			Foreground(primary).
			Bold(true).
			Padding(0, 1),

		Subtitle: lipgloss.NewStyle().
			Foreground(secondary).
			Italic(true).
			Padding(0, 1),

		Header: lipgloss.NewStyle().
			Foreground(foreground).
			Bold(true).
			BorderStyle(lipgloss.NormalBorder()).
			BorderBottom(true).
			BorderForeground(border).
			Padding(0, 1, 1, 1),

		Footer: lipgloss.NewStyle().
			Foreground(dimmed).
			BorderStyle(lipgloss.NormalBorder()).
			BorderTop(true).
			BorderForeground(border).
			Padding(1, 1, 0, 1),

		Help: lipgloss.NewStyle().
			Foreground(dimmed),

		Error: lipgloss.NewStyle().
			Foreground(errorColor).
			Bold(true),

		Success: lipgloss.NewStyle().
			Foreground(success).
			Bold(true),

		Warning: lipgloss.NewStyle().
			Foreground(warning).
			Bold(true),

		Info: lipgloss.NewStyle().
			Foreground(secondary),

		// Layout styles
		Box: lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(border).
			Padding(1, 2),

		ActiveBox: lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(activeBorder).
			Padding(1, 2),

		Border: lipgloss.NewStyle().
			BorderStyle(lipgloss.NormalBorder()).
			BorderForeground(border),

		ActiveBorder: lipgloss.NewStyle().
			BorderStyle(lipgloss.NormalBorder()).
			BorderForeground(activeBorder),

		// Interactive element styles
		Button: lipgloss.NewStyle().
			Foreground(foreground).
			Background(border).
			Padding(0, 2).
			Margin(0, 1),

		ActiveButton: lipgloss.NewStyle().
			Foreground(background).
			Background(primary).
			Bold(true).
			Padding(0, 2).
			Margin(0, 1),

		Input: lipgloss.NewStyle().
			Foreground(foreground).
			BorderStyle(lipgloss.NormalBorder()).
			BorderForeground(border).
			Padding(0, 1),

		InputFocus: lipgloss.NewStyle().
			Foreground(foreground).
			BorderStyle(lipgloss.NormalBorder()).
			BorderForeground(primary).
			Padding(0, 1),

		// Status indicator styles
		Healthy: lipgloss.NewStyle().
			Foreground(success).
			Bold(true),

		Unhealthy: lipgloss.NewStyle().
			Foreground(errorColor).
			Bold(true),

		Disabled: lipgloss.NewStyle().
			Foreground(dimmed),

		Pending: lipgloss.NewStyle().
			Foreground(warning).
			Bold(true),
	}
}

// SaveThemes saves the current themes to the themes.yaml file
func (tm *ThemeManager) SaveThemes() error {
	themesPath := filepath.Join(tm.dotfilesPath, "templates", "themes.yaml")

	// Ensure directory exists
	dir := filepath.Dir(themesPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create themes directory: %w", err)
	}

	// Create config structure
	config := ThemeConfig{
		Themes: tm.themes,
	}

	// Marshal to YAML
	data, err := yaml.Marshal(&config)
	if err != nil {
		return fmt.Errorf("failed to marshal themes: %w", err)
	}

	// Add header comment
	header := "# Dotfiles Manager Theme Configuration\n# Customize the appearance of the TUI interface\n\n"
	finalData := append([]byte(header), data...)

	// Write to file
	if err := os.WriteFile(themesPath, finalData, 0644); err != nil {
		return fmt.Errorf("failed to write themes file: %w", err)
	}

	return nil
}

// AddTheme adds a new custom theme
func (tm *ThemeManager) AddTheme(name string, theme Theme) {
	theme.Name = name
	tm.themes[name] = theme
	tm.cachedStyles = nil // Clear cache
}

// RemoveTheme removes a theme (except default themes)
func (tm *ThemeManager) RemoveTheme(name string) error {
	// Protect default themes
	if name == "default" || name == "light" || name == "cyberpunk" {
		return fmt.Errorf("cannot remove built-in theme '%s'", name)
	}

	if _, exists := tm.themes[name]; !exists {
		return fmt.Errorf("theme '%s' not found", name)
	}

	// Switch to default if removing current theme
	if tm.currentTheme == name {
		tm.currentTheme = "default"
		tm.cachedStyles = nil
	}

	delete(tm.themes, name)
	return nil
}

// CreateThemeFromCurrent creates a new theme based on the current theme
func (tm *ThemeManager) CreateThemeFromCurrent(name string) Theme {
	current := tm.GetCurrentThemeData()
	newTheme := Theme{
		Name:       name,
		Primary:    current.Primary,
		Secondary:  current.Secondary,
		Success:    current.Success,
		Warning:    current.Warning,
		Error:      current.Error,
		Background: current.Background,
		Foreground: current.Foreground,
	}
	return newTheme
}
