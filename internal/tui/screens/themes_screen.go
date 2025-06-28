package screens

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/list"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/yourusername/dotfiles/internal/config"
	"github.com/yourusername/dotfiles/internal/theme"
)

// ThemesScreen manages theme selection and customization
type ThemesScreen struct {
	config       *config.Config
	themeManager *theme.ThemeManager
	list         list.Model
	width        int
	height       int
	currentTheme string
}


// ThemeItem represents a theme option
type ThemeItem struct {
	name        string
	description string
	preview     ThemePreview
}

// ThemePreview contains color information for preview
type ThemePreview struct {
	Primary    string
	Secondary  string
	Success    string
	Warning    string
	Error      string
	Background string
	Foreground string
}

func (t ThemeItem) FilterValue() string { return t.name }
func (t ThemeItem) Title() string       { return t.name }
func (t ThemeItem) Description() string { return t.description }

// ThemeChangedMsg indicates a theme has been selected
type ThemeChangedMsg struct {
	ThemeName string
}

// NewThemesScreen creates a new themes screen
func NewThemesScreen(cfg *config.Config, themeManager *theme.ThemeManager, width, height int) ThemesScreen {
	// Get available themes from theme manager
	availableThemes := themeManager.GetThemes()
	themes := make([]list.Item, 0, len(availableThemes))
	
	// Define theme descriptions
	descriptions := map[string]string{
		"default":         "🌟 Classic terminal theme with green accents",
		"light":           "☀️ Clean light theme for daytime use", 
		"cyberpunk":       "🌆 Neon-inspired theme with vibrant colors",
		"solarized_dark":  "🌙 Popular Solarized dark color scheme",
		"solarized_light": "☀️ Popular Solarized light color scheme",
	}
	
	for name, themeData := range availableThemes {
		description := descriptions[name]
		if description == "" {
			description = "🎨 Custom theme"
		}
		
		themes = append(themes, ThemeItem{
			name:        strings.Title(name),
			description: description,
			preview: ThemePreview{
				Primary:    themeData.Primary,
				Secondary:  themeData.Secondary,
				Success:    themeData.Success,
				Warning:    themeData.Warning,
				Error:      themeData.Error,
				Background: themeData.Background,
				Foreground: themeData.Foreground,
			},
		})
	}

	// Get theme styles
	styles := themeManager.GetStyles()
	
	// Create list with themed delegate
	delegate := list.NewDefaultDelegate()
	delegate.Styles.SelectedTitle = styles.ActiveButton
	delegate.Styles.SelectedDesc = styles.Info

	l := list.New(themes, delegate, width-20, height-8) // Leave space for preview
	l.Title = "Available Themes"
	l.SetShowStatusBar(false)
	l.SetFilteringEnabled(true)
	l.Styles.Title = styles.Title

	return ThemesScreen{
		config:       cfg,
		themeManager: themeManager,
		list:         l,
		width:        width,
		height:       height,
		currentTheme: cfg.TUI.ColorScheme,
	}
}

// Init initializes the themes screen
func (ts ThemesScreen) Init() tea.Cmd {
	return nil
}

// Update handles themes screen updates
func (ts ThemesScreen) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		ts.width = msg.Width
		ts.height = msg.Height
		ts.list.SetSize(msg.Width-20, msg.Height-8)

	case tea.KeyMsg:
		switch msg.String() {
		case "enter":
			// Apply selected theme
			selected := ts.list.SelectedItem()
			if themeItem, ok := selected.(ThemeItem); ok {
				ts.currentTheme = themeItem.name
				return ts, func() tea.Msg {
					return ThemeChangedMsg{ThemeName: themeItem.name}
				}
			}
		case "q", "esc":
			return ts, tea.Quit
		}

		// Forward to list for navigation
		ts.list, cmd = ts.list.Update(msg)
	}

	return ts, cmd
}

// View renders the themes screen
func (ts ThemesScreen) View() string {
	// Split screen into list and preview
	listWidth := (ts.width * 3) / 5 // 60% for list
	previewWidth := ts.width - listWidth - 4 // Rest for preview

	ts.list.SetSize(listWidth, ts.height-6)

	// Render components
	header := ts.renderHeader()
	listView := ts.list.View()
	preview := ts.renderPreview(previewWidth)
	footer := ts.renderFooter()

	// Create main content with side-by-side layout
	mainContent := lipgloss.JoinHorizontal(
		lipgloss.Top,
		listView,
		preview,
	)

	// Combine all sections
	return lipgloss.JoinVertical(
		lipgloss.Left,
		header,
		mainContent,
		footer,
	)
}

func (ts ThemesScreen) renderHeader() string {
	styles := ts.themeManager.GetStyles()
	title := "🎨 Theme Selection"
	currentInfo := fmt.Sprintf("Current: %s", ts.currentTheme)
	headerContent := lipgloss.JoinHorizontal(
		lipgloss.Left,
		styles.Title.Render(title),
		styles.Help.Render(" • "+currentInfo),
	)
	return styles.Header.Width(ts.width-2).Render(headerContent)
}

func (ts ThemesScreen) renderPreview(width int) string {
	styles := ts.themeManager.GetStyles()
	selected := ts.list.SelectedItem()
	if themeItem, ok := selected.(ThemeItem); ok {
		return ts.renderThemePreview(themeItem, width)
	}
	return styles.Box.Width(width).Render("Select a theme to preview")
}

func (ts ThemesScreen) renderThemePreview(theme ThemeItem, width int) string {
	preview := theme.preview

	// Create color swatches
	var swatches []string
	swatches = append(swatches, ts.renderColorSwatch("Primary", preview.Primary))
	swatches = append(swatches, ts.renderColorSwatch("Secondary", preview.Secondary))
	swatches = append(swatches, ts.renderColorSwatch("Success", preview.Success))
	swatches = append(swatches, ts.renderColorSwatch("Warning", preview.Warning))
	swatches = append(swatches, ts.renderColorSwatch("Error", preview.Error))

	// Create sample UI elements with theme colors
	sampleUI := ts.renderSampleUI(preview)

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		lipgloss.NewStyle().Bold(true).Render(fmt.Sprintf("Preview: %s", theme.name)),
		"",
		lipgloss.NewStyle().Bold(true).Render("Color Palette:"),
		strings.Join(swatches, "\n"),
		"",
		lipgloss.NewStyle().Bold(true).Render("Sample Interface:"),
		sampleUI,
	)

	styles := ts.themeManager.GetStyles()
	return styles.Box.Width(width).Render(content)
}

func (ts ThemesScreen) renderColorSwatch(name, color string) string {
	// Create a colored block followed by the color name and hex
	colorBlock := lipgloss.NewStyle().
		Background(lipgloss.Color(color)).
		Foreground(lipgloss.Color(color)).
		Render("████")

	label := fmt.Sprintf(" %-9s %s", name+":", color)
	return colorBlock + label
}

func (ts ThemesScreen) renderSampleUI(preview ThemePreview) string {
	// Create sample UI elements using the theme colors
	titleStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(preview.Primary)).
		Bold(true)

	successStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(preview.Success))

	warningStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(preview.Warning))

	errorStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(preview.Error))

	sampleElements := []string{
		titleStyle.Render("📦 Sample Tool Status"),
		successStyle.Render("✅ Package installed successfully"),
		warningStyle.Render("⚠️  Update available for package"),
		errorStyle.Render("❌ Failed to install package"),
		lipgloss.NewStyle().Foreground(lipgloss.Color(preview.Foreground)).Render("   Regular status text"),
	}

	return strings.Join(sampleElements, "\n")
}

func (ts ThemesScreen) renderFooter() string {
	styles := ts.themeManager.GetStyles()
	help := []string{
		"[enter] apply theme",
		"[↑/↓] navigate",
		"[/] filter",
		"[q/esc] back",
	}
	return styles.Footer.Width(ts.width-2).Render(
		styles.Help.Render(strings.Join(help, " • ")),
	)
}
