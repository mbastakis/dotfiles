package models

import (
	tea "github.com/charmbracelet/bubbletea"
	"github.com/yourusername/dotfiles/internal/config"
	"github.com/yourusername/dotfiles/internal/theme"
	"github.com/yourusername/dotfiles/internal/tools"
	"github.com/yourusername/dotfiles/internal/tui/screens"
)

// AppModel represents the root application model that handles navigation
type AppModel struct {
	config       *config.Config
	registry     *tools.ToolRegistry
	themeManager *theme.ThemeManager
	currentScreen Screen
	screenStack  []Screen
	width        int
	height       int
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
	OverviewScreen
	SettingsScreen
	ThemesScreen
)

// NavigateMsg represents navigation to a new screen
type NavigateMsg struct {
	Screen Screen
}

// BackMsg represents going back to the previous screen
type BackMsg struct{}

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

	case NavigateMsg:
		// Push current screen to stack and navigate to new screen
		a.screenStack = append(a.screenStack, a.currentScreen)
		a.currentScreen = msg.Screen
		return a, a.currentScreen.Init()

	case BackMsg:
		// Pop screen from stack
		if len(a.screenStack) > 0 {
			a.currentScreen = a.screenStack[len(a.screenStack)-1]
			a.screenStack = a.screenStack[:len(a.screenStack)-1]
		}
		return a, nil

	case tea.KeyMsg:
		// Handle global navigation keys
		switch msg.String() {
		case "esc", "q":
			// Go back if we're not on the main screen
			if len(a.screenStack) > 0 {
				return a.Update(BackMsg{})
			}
			// If on main screen and 'q' is pressed, quit
			if msg.String() == "q" && len(a.screenStack) == 0 {
				return a, tea.Quit
			}
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

	return a.Update(NavigateMsg{Screen: newScreen})
}