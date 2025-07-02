package models

import (
	"os"
	"path/filepath"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/mbastakis/dotfiles/internal/common"
	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/theme"
	"github.com/mbastakis/dotfiles/internal/tools"
	"github.com/mbastakis/dotfiles/internal/tui/screens"
)

// AppModel represents the root application model that handles navigation
type AppModel struct {
	config        *config.Config
	registry      *tools.ToolRegistry
	themeManager  *theme.ThemeManager
	currentScreen Screen
	screenStack   []Screen
	width         int
	height        int
}

// Screen represents a screen in the application
type Screen interface {
	tea.Model
}

// ScreenType represents the type of screen
type ScreenType int

const (
	MainMenuScreen ScreenType = iota
	ToolScreen
	CategoryDetailScreen
	OverviewScreen
	SettingsScreen
	ThemesScreen
)

// NewAppModel creates a new application model
func NewAppModel(cfg *config.Config, registry *tools.ToolRegistry, themeManager *theme.ThemeManager) AppModel {
	mainModel := NewMainModel(cfg, registry, themeManager)

	return AppModel{
		config:        cfg,
		registry:      registry,
		themeManager:  themeManager,
		currentScreen: mainModel,
		screenStack:   make([]Screen, 0),
	}
}

// Init initializes the application model
func (a AppModel) Init() tea.Cmd {
	return a.currentScreen.Init()
}

// Update handles application-level updates and navigation
func (a AppModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		a.width = msg.Width
		a.height = msg.Height
		// Forward to current screen
		newScreen, cmd := a.currentScreen.Update(msg)
		a.currentScreen = newScreen
		return a, cmd

	case common.NavigateMsg:
		// Push current screen to stack and navigate to new screen
		a.screenStack = append(a.screenStack, a.currentScreen)
		a.currentScreen = msg.Screen

		// Initialize the new screen and send it the current window size
		cmds := []tea.Cmd{a.currentScreen.Init()}
		if a.width > 0 && a.height > 0 {
			// Send window size to the new screen
			newScreen, sizeCmd := a.currentScreen.Update(tea.WindowSizeMsg{
				Width:  a.width,
				Height: a.height,
			})
			a.currentScreen = newScreen
			if sizeCmd != nil {
				cmds = append(cmds, sizeCmd)
			}
		}
		return a, tea.Batch(cmds...)

	case common.BackMsg:
		// Pop screen from stack
		if len(a.screenStack) > 0 {
			a.currentScreen = a.screenStack[len(a.screenStack)-1]
			a.screenStack = a.screenStack[:len(a.screenStack)-1]
		}
		return a, nil

	case screens.ThemeChangedMsg:
		// Handle theme change
		themeName := msg.ThemeName

		// Apply the theme to the theme manager
		if err := a.themeManager.SetCurrentTheme(strings.ToLower(themeName)); err != nil {
			return a, tea.Printf("Failed to apply theme: %v", err)
		}

		// Update the config
		a.config.TUI.ColorScheme = strings.ToLower(themeName)

		// Save config to the standard location
		homeDir, _ := os.UserHomeDir()
		configPath := filepath.Join(homeDir, ".config", "dotfiles", "config.yaml")
		if err := a.config.Save(configPath); err != nil {
			return a, tea.Printf("Failed to save config: %v", err)
		}

		// Recreate all screens with the new theme
		// First recreate the current screen
		if _, ok := a.currentScreen.(screens.ThemesScreen); ok {
			a.currentScreen = screens.NewThemesScreen(a.config, a.themeManager, a.width, a.height)
		}

		// Clear and recreate the screen stack
		newStack := make([]Screen, 0, len(a.screenStack))
		for _, screen := range a.screenStack {
			// Recreate main menu screens
			if _, ok := screen.(MainModel); ok {
				newStack = append(newStack, NewMainModel(a.config, a.registry, a.themeManager))
			} else {
				// For now, keep other screens as is (they'll be recreated when navigated to)
				newStack = append(newStack, screen)
			}
		}
		a.screenStack = newStack

		// Send window size update to refresh the current screen
		if a.width > 0 && a.height > 0 {
			newScreen, cmd := a.currentScreen.Update(tea.WindowSizeMsg{
				Width:  a.width,
				Height: a.height,
			})
			a.currentScreen = newScreen
			return a, cmd
		}

		return a, nil

	case tea.KeyMsg:
		// Handle global navigation keys
		switch msg.String() {
		case "esc", "q":
			// Go back if we're not on the main screen
			if len(a.screenStack) > 0 {
				return a.Update(common.BackMsg{})
			}
			// If on main screen and 'q' is pressed, quit
			if msg.String() == "q" && len(a.screenStack) == 0 {
				return a, tea.Quit
			}
		case "s":
			// Navigate to overview screen from any screen
			overviewScreen := screens.NewOverviewScreen(a.config, a.registry, a.themeManager, a.width, a.height)
			return a.Update(common.NavigateMsg{Screen: overviewScreen})
		}

		// Check if this is navigation from the main menu
		if mainModel, ok := a.currentScreen.(MainModel); ok {
			return a.handleMainMenuNavigation(mainModel, msg)
		}

		// Forward to current screen
		newScreen, cmd := a.currentScreen.Update(msg)
		a.currentScreen = newScreen
		return a, cmd

	default:
		// Forward to current screen
		newScreen, cmd := a.currentScreen.Update(msg)
		a.currentScreen = newScreen
		return a, cmd
	}
}

// View renders the current screen
func (a AppModel) View() string {
	return a.currentScreen.View()
}

// handleMainMenuNavigation handles navigation from the main menu
func (a AppModel) handleMainMenuNavigation(mainModel MainModel, msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	// First, update the main model to handle selection
	newMainModel, cmd := mainModel.Update(msg)
	a.currentScreen = newMainModel

	// Check if Enter was pressed to navigate
	if msg.String() == "enter" {
		selected := mainModel.list.SelectedItem()
		if menuItem, ok := selected.(MenuItem); ok {
			return a.navigateToScreen(menuItem)
		}
	}

	return a, cmd
}

// navigateToScreen creates and navigates to the appropriate screen
func (a AppModel) navigateToScreen(menuItem MenuItem) (tea.Model, tea.Cmd) {
	var newScreen Screen

	if menuItem.tool != nil {
		// Navigate to tool-specific screen
		toolScreen := screens.NewToolScreen(menuItem.tool, a.themeManager, a.width, a.height)
		newScreen = toolScreen
	} else {
		// Handle special screens based on title
		switch menuItem.title {
		case "🏠 Overview":
			overviewScreen := screens.NewOverviewScreen(a.config, a.registry, a.themeManager, a.width, a.height)
			newScreen = overviewScreen
		case "🎨 Themes":
			themesScreen := screens.NewThemesScreen(a.config, a.themeManager, a.width, a.height)
			newScreen = themesScreen
		case "⚙️  Settings":
			settingsScreen := screens.NewSettingsScreen(a.config, a.themeManager, a.width, a.height)
			newScreen = settingsScreen
		default:
			return a, tea.Printf("Unknown screen: %s", menuItem.title)
		}
	}

	return a.Update(common.NavigateMsg{Screen: newScreen})
}
