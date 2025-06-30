package models

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/list"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/theme"
	"github.com/mbastakis/dotfiles/internal/tools"
)

// MainModel represents the main TUI model
type MainModel struct {
	config       *config.Config
	registry     *tools.ToolRegistry
	themeManager *theme.ThemeManager
	list         list.Model
	keys         keyMap
	width        int
	height       int
	ready        bool
}

// MenuItem represents a menu item
type MenuItem struct {
	title       string
	description string
	tool        tools.Tool
}

func (m MenuItem) Title() string       { return m.title }
func (m MenuItem) Description() string { return m.description }
func (m MenuItem) FilterValue() string { return m.title }

type keyMap struct {
	Up     key.Binding
	Down   key.Binding
	Enter  key.Binding
	Quit   key.Binding
	Help   key.Binding
	Status key.Binding
}

func (k keyMap) ShortHelp() []key.Binding {
	return []key.Binding{k.Enter, k.Status, k.Quit, k.Help}
}

func (k keyMap) FullHelp() [][]key.Binding {
	return [][]key.Binding{
		{k.Up, k.Down, k.Enter},
		{k.Status, k.Quit, k.Help},
	}
}

var keys = keyMap{
	Up: key.NewBinding(
		key.WithKeys("up", "k"),
		key.WithHelp("↑/k", "move up"),
	),
	Down: key.NewBinding(
		key.WithKeys("down", "j"),
		key.WithHelp("↓/j", "move down"),
	),
	Enter: key.NewBinding(
		key.WithKeys("enter"),
		key.WithHelp("enter", "select"),
	),
	Quit: key.NewBinding(
		key.WithKeys("q", "ctrl+c"),
		key.WithHelp("q", "quit"),
	),
	Help: key.NewBinding(
		key.WithKeys("?"),
		key.WithHelp("?", "help"),
	),
	Status: key.NewBinding(
		key.WithKeys("s"),
		key.WithHelp("s", "status"),
	),
}

// NewMainModel creates a new main model
func NewMainModel(cfg *config.Config, registry *tools.ToolRegistry, themeManager *theme.ThemeManager) MainModel {
	// Create menu items for enabled tools
	var items []list.Item
	
	// Add overview item
	items = append(items, MenuItem{
		title:       "🏠 Overview",
		description: "📊 Current system status",
		tool:        nil,
	})

	// Add tool-specific items
	for _, tool := range registry.GetByPriority() {
		var icon string
		var desc string
		
		switch tool.Name() {
		case "stow":
			icon = "📦"
			desc = "🔗 Manage symlinked packages"
		case "rsync":
			icon = "📋"
			desc = "🚀 Manage file synchronization"
		case "homebrew":
			icon = "🍺"
			desc = "📦 Package management"
		case "npm":
			icon = "📱"
			desc = "🌐 Global Node.js packages"
		case "uv":
			icon = "🐍"
			desc = "🛠️  Python tool packages"
		case "apps":
			icon = "⚙️"
			desc = "🔧 Custom application scripts"
		default:
			icon = "🔧"
			desc = "Tool management"
		}
		
		items = append(items, MenuItem{
			title:       fmt.Sprintf("%s %s", icon, strings.Title(tool.Name())),
			description: desc,
			tool:        tool,
		})
	}

	// Add additional items
	items = append(items, MenuItem{
		title:       "🎨 Themes",
		description: "🖌️  UI customization",
		tool:        nil,
	})
	
	items = append(items, MenuItem{
		title:       "⚙️  Settings",
		description: "⚙️  Configuration management",
		tool:        nil,
	})

	// Get theme styles
	styles := themeManager.GetStyles()
	
	// Create list with themed delegate
	delegate := list.NewDefaultDelegate()
	delegate.Styles.SelectedTitle = styles.ActiveButton
	delegate.Styles.SelectedDesc = styles.Info

	l := list.New(items, delegate, 0, 0)
	l.Title = "Dotfiles Manager"
	l.SetShowStatusBar(false)
	l.SetFilteringEnabled(false)
	l.Styles.Title = styles.Title

	return MainModel{
		config:       cfg,
		registry:     registry,
		themeManager: themeManager,
		list:         l,
		keys:         keys,
	}
}

func (m MainModel) Init() tea.Cmd {
	return nil
}

func (m MainModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.list.SetSize(msg.Width-4, msg.Height-4)
		m.ready = true
		return m, nil

	case tea.KeyMsg:
		switch {
		case key.Matches(msg, m.keys.Quit):
			return m, tea.Quit

		case key.Matches(msg, m.keys.Enter):
			// Don't handle Enter here - let the app model handle navigation
			// Just forward the key event to the list component

		case key.Matches(msg, m.keys.Status):
			// Don't handle Status here - let the app model handle it
			// Just forward the key event to the list component
		}
	}

	var cmd tea.Cmd
	m.list, cmd = m.list.Update(msg)
	return m, cmd
}

func (m MainModel) View() string {
	if !m.ready {
		return "Loading..."
	}

	// Create the main layout
	content := lipgloss.JoinVertical(
		lipgloss.Left,
		m.list.View(),
		m.helpView(),
	)

	return lipgloss.Place(
		m.width, m.height,
		lipgloss.Center, lipgloss.Center,
		content,
	)
}

func (m MainModel) helpView() string {
	help := []string{
		"Press Enter to select, q to quit, ? for help",
		"Use ↑/↓ or j/k to navigate, s for status",
	}
	
	styles := m.themeManager.GetStyles()
	return styles.Help.Render(strings.Join(help, " • "))
}