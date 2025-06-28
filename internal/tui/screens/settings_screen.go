package screens

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/charmbracelet/bubbles/list"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/yourusername/dotfiles/internal/config"
	"github.com/yourusername/dotfiles/internal/theme"
)

// SettingsScreen manages configuration options
type SettingsScreen struct {
	config         *config.Config
	themeManager   *theme.ThemeManager
	list           list.Model
	textInput      textinput.Model
	width          int
	height         int
	editMode       bool
	currentSetting *SettingItem
}


// SettingItem represents a configurable setting
type SettingItem struct {
	key         string
	name        string
	description string
	value       string
	settingType SettingType
	options     []string // For enum types
	validation  func(string) error
}

// SettingType defines the type of setting
type SettingType int

const (
	StringSetting SettingType = iota
	BoolSetting
	IntSetting
	EnumSetting
	PathSetting
)

func (s SettingItem) FilterValue() string { return s.name }
func (s SettingItem) Title() string       { return s.name }
func (s SettingItem) Description() string {
	return fmt.Sprintf("%s (Current: %s)", s.description, s.value)
}

// SettingChangedMsg indicates a setting has been changed
type SettingChangedMsg struct {
	Key   string
	Value string
}

// NewSettingsScreen creates a new settings screen
func NewSettingsScreen(cfg *config.Config, themeManager *theme.ThemeManager, width, height int) SettingsScreen {
	// Define configurable settings
	settings := []list.Item{
		SettingItem{
			key:         "global.log_level",
			name:        "Log Level",
			description: "Logging verbosity level",
			value:       cfg.Global.LogLevel,
			settingType: EnumSetting,
			options:     []string{"debug", "info", "warn", "error"},
		},
		SettingItem{
			key:         "global.dry_run",
			name:        "Dry Run Mode",
			description: "Show what would be done without executing",
			value:       strconv.FormatBool(cfg.Global.DryRun),
			settingType: BoolSetting,
		},
		SettingItem{
			key:         "global.auto_confirm",
			name:        "Auto Confirm",
			description: "Automatically confirm prompts",
			value:       strconv.FormatBool(cfg.Global.AutoConfirm),
			settingType: BoolSetting,
		},
		SettingItem{
			key:         "global.backup_enabled",
			name:        "Backup Enabled",
			description: "Create backups before destructive operations",
			value:       strconv.FormatBool(cfg.Global.BackupEnabled),
			settingType: BoolSetting,
		},
		SettingItem{
			key:         "global.backup_suffix",
			name:        "Backup Suffix",
			description: "Suffix for backup files",
			value:       cfg.Global.BackupSuffix,
			settingType: StringSetting,
		},
		SettingItem{
			key:         "global.dotfiles_path",
			name:        "Dotfiles Path",
			description: "Path to dotfiles repository",
			value:       cfg.Global.DotfilesPath,
			settingType: PathSetting,
		},
		SettingItem{
			key:         "tui.color_scheme",
			name:        "Color Scheme",
			description: "TUI color theme",
			value:       cfg.TUI.ColorScheme,
			settingType: EnumSetting,
			options:     []string{"default", "light", "cyberpunk", "solarized", "dracula"},
		},
		SettingItem{
			key:         "tui.animations",
			name:        "Animations",
			description: "Enable TUI animations",
			value:       strconv.FormatBool(cfg.TUI.Animations),
			settingType: BoolSetting,
		},
		SettingItem{
			key:         "tui.confirm_destructive",
			name:        "Confirm Destructive Actions",
			description: "Ask for confirmation before destructive operations",
			value:       strconv.FormatBool(cfg.TUI.ConfirmDestructive),
			settingType: BoolSetting,
		},
		SettingItem{
			key:         "tui.show_progress",
			name:        "Show Progress",
			description: "Display progress bars for operations",
			value:       strconv.FormatBool(cfg.TUI.ShowProgress),
			settingType: BoolSetting,
		},
	}

	// Get theme styles
	styles := themeManager.GetStyles()
	
	// Create list with themed delegate
	delegate := list.NewDefaultDelegate()
	delegate.Styles.SelectedTitle = styles.ActiveButton
	delegate.Styles.SelectedDesc = styles.Info

	l := list.New(settings, delegate, width-4, height-8)
	l.Title = "Configuration Settings"
	l.SetShowStatusBar(false)
	l.SetFilteringEnabled(true)
	l.Styles.Title = styles.Title

	// Create text input for editing with themed styles
	ti := textinput.New()
	ti.CharLimit = 256
	ti.Width = width - 20
	ti.PromptStyle = styles.Input
	ti.TextStyle = styles.Input

	return SettingsScreen{
		config:       cfg,
		themeManager: themeManager,
		list:         l,
		textInput:    ti,
		width:        width,
		height:       height,
	}
}

// Init initializes the settings screen
func (ss SettingsScreen) Init() tea.Cmd {
	return nil
}

// Update handles settings screen updates
func (ss SettingsScreen) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		ss.width = msg.Width
		ss.height = msg.Height
		ss.list.SetSize(msg.Width-4, msg.Height-8)
		ss.textInput.Width = msg.Width - 20

	case tea.KeyMsg:
		if ss.editMode {
			return ss.handleEditMode(msg)
		}

		switch msg.String() {
		case "enter":
			// Start editing selected setting
			selected := ss.list.SelectedItem()
			if settingItem, ok := selected.(SettingItem); ok {
				return ss.startEditing(settingItem)
			}
		case "r":
			// Reset to default value
			selected := ss.list.SelectedItem()
			if settingItem, ok := selected.(SettingItem); ok {
				return ss.resetSetting(settingItem)
			}
		case "q", "esc":
			return ss, tea.Quit
		}

		// Forward to list for navigation
		ss.list, cmd = ss.list.Update(msg)
	}

	return ss, cmd
}

// View renders the settings screen
func (ss SettingsScreen) View() string {
	if ss.editMode {
		return ss.renderEditMode()
	}

	var sections []string

	// Header
	header := ss.renderHeader()
	sections = append(sections, header)

	// Main list
	listView := ss.list.View()
	sections = append(sections, listView)

	// Footer with help
	footer := ss.renderFooter()
	sections = append(sections, footer)

	return lipgloss.JoinVertical(lipgloss.Left, sections...)
}

func (ss SettingsScreen) renderHeader() string {
	styles := ss.themeManager.GetStyles()
	title := "⚙️ Configuration Settings"
	subtitle := "Modify application behavior and preferences"
	headerContent := lipgloss.JoinVertical(
		lipgloss.Left,
		styles.Title.Render(title),
		styles.Subtitle.Render(subtitle),
	)
	return styles.Header.Width(ss.width-2).Render(headerContent)
}

func (ss SettingsScreen) renderFooter() string {
	styles := ss.themeManager.GetStyles()
	help := []string{
		"[enter] edit setting",
		"[r] reset to default",
		"[↑/↓] navigate",
		"[/] filter",
		"[q/esc] back",
	}
	return styles.Footer.Width(ss.width-2).Render(
		styles.Help.Render(strings.Join(help, " • ")),
	)
}

func (ss SettingsScreen) renderEditMode() string {
	if ss.currentSetting == nil {
		return "Error: No setting selected for editing"
	}

	styles := ss.themeManager.GetStyles()
	
	// Create edit interface based on setting type
	var content []string

	content = append(content, styles.Title.Render(
		fmt.Sprintf("Editing: %s", ss.currentSetting.name),
	))
	content = append(content, "")
	content = append(content, styles.Subtitle.Render(ss.currentSetting.description))
	content = append(content, "")

	switch ss.currentSetting.settingType {
	case BoolSetting:
		content = append(content, "Current value: "+styles.Success.Render(ss.currentSetting.value))
		content = append(content, "")
		content = append(content, "Press [y] for true, [n] for false, [esc] to cancel")

	case EnumSetting:
		content = append(content, "Current value: "+styles.Success.Render(ss.currentSetting.value))
		content = append(content, "")
		content = append(content, "Available options:")
		for i, option := range ss.currentSetting.options {
			prefix := "  "
			if option == ss.currentSetting.value {
				prefix = "▶ "
			}
			content = append(content, fmt.Sprintf("%s[%d] %s", prefix, i+1, option))
		}
		content = append(content, "")
		content = append(content, "Press number key to select, [esc] to cancel")

	default:
		content = append(content, "Enter new value:")
		content = append(content, ss.textInput.View())
		content = append(content, "")
		content = append(content, "Press [enter] to save, [esc] to cancel")
	}

	mainContent := strings.Join(content, "\n")
	return styles.ActiveBox.Width(ss.width-4).Render(mainContent)
}

func (ss SettingsScreen) startEditing(setting SettingItem) (SettingsScreen, tea.Cmd) {
	ss.editMode = true
	ss.currentSetting = &setting

	// Initialize text input for string-based settings
	if setting.settingType == StringSetting || setting.settingType == PathSetting {
		ss.textInput.SetValue(setting.value)
		ss.textInput.Focus()
		return ss, textinput.Blink
	}

	return ss, nil
}

func (ss SettingsScreen) handleEditMode(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	if ss.currentSetting == nil {
		ss.editMode = false
		return ss, nil
	}

	switch msg.String() {
	case "esc":
		// Cancel editing
		ss.editMode = false
		ss.currentSetting = nil
		ss.textInput.Blur()
		return ss, nil

	case "enter":
		if ss.currentSetting.settingType == StringSetting || ss.currentSetting.settingType == PathSetting {
			// Save string value
			newValue := ss.textInput.Value()
			return ss.saveSetting(ss.currentSetting.key, newValue)
		}

	case "y":
		if ss.currentSetting.settingType == BoolSetting {
			return ss.saveSetting(ss.currentSetting.key, "true")
		}

	case "n":
		if ss.currentSetting.settingType == BoolSetting {
			return ss.saveSetting(ss.currentSetting.key, "false")
		}

	case "1", "2", "3", "4", "5", "6", "7", "8", "9":
		if ss.currentSetting.settingType == EnumSetting {
			index, _ := strconv.Atoi(msg.String())
			if index > 0 && index <= len(ss.currentSetting.options) {
				selectedValue := ss.currentSetting.options[index-1]
				return ss.saveSetting(ss.currentSetting.key, selectedValue)
			}
		}
	}

	// Forward to text input if it's a string-based setting
	if ss.currentSetting.settingType == StringSetting || ss.currentSetting.settingType == PathSetting {
		var cmd tea.Cmd
		ss.textInput, cmd = ss.textInput.Update(msg)
		return ss, cmd
	}

	return ss, nil
}

func (ss SettingsScreen) saveSetting(key, value string) (SettingsScreen, tea.Cmd) {
	// Update the current setting value
	if ss.currentSetting != nil {
		ss.currentSetting.value = value
		// Update the list item
		ss.updateListItem(*ss.currentSetting)
	}

	// Exit edit mode
	ss.editMode = false
	ss.currentSetting = nil
	ss.textInput.Blur()

	// Return message about the change
	return ss, func() tea.Msg {
		return SettingChangedMsg{Key: key, Value: value}
	}
}

func (ss SettingsScreen) resetSetting(setting SettingItem) (SettingsScreen, tea.Cmd) {
	// This would reset to default values - implementation depends on how defaults are stored
	defaultValue := ss.getDefaultValue(setting.key)
	return ss.saveSetting(setting.key, defaultValue)
}

func (ss SettingsScreen) getDefaultValue(key string) string {
	// Return default values for each setting
	defaults := map[string]string{
		"global.log_level":           "info",
		"global.dry_run":             "false",
		"global.auto_confirm":        "false",
		"global.backup_enabled":      "true",
		"global.backup_suffix":       ".backup",
		"global.dotfiles_path":       "~/dev/dotfiles",
		"tui.color_scheme":           "default",
		"tui.animations":             "true",
		"tui.confirm_destructive":    "true",
		"tui.show_progress":          "true",
	}

	if defaultVal, exists := defaults[key]; exists {
		return defaultVal
	}
	return ""
}

func (ss *SettingsScreen) updateListItem(updatedSetting SettingItem) {
	// Find and update the corresponding list item
	items := ss.list.Items()
	for i, item := range items {
		if settingItem, ok := item.(SettingItem); ok {
			if settingItem.key == updatedSetting.key {
				items[i] = updatedSetting
				ss.list.SetItems(items)
				break
			}
		}
	}
}
