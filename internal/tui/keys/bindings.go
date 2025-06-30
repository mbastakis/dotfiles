package keys

import (
	"github.com/charmbracelet/bubbles/key"
)

// ToolKeyMap defines keybindings for tool operations
type ToolKeyMap struct {
	Install key.Binding
	Update  key.Binding
	Remove  key.Binding
	Sync    key.Binding
	Refresh key.Binding
	Select  key.Binding
	Back    key.Binding
	Help    key.Binding
}

// DefaultToolKeyMap returns the default keybindings for tool operations
func DefaultToolKeyMap() ToolKeyMap {
	return ToolKeyMap{
		Install: key.NewBinding(
			key.WithKeys("i"),
			key.WithHelp("i", "install selected"),
		),
		Update: key.NewBinding(
			key.WithKeys("u"),
			key.WithHelp("u", "update selected"),
		),
		Remove: key.NewBinding(
			key.WithKeys("d"),
			key.WithHelp("d", "delete/remove selected"),
		),
		Sync: key.NewBinding(
			key.WithKeys("s"),
			key.WithHelp("s", "sync all"),
		),
		Refresh: key.NewBinding(
			key.WithKeys("r"),
			key.WithHelp("r", "refresh status"),
		),
		Select: key.NewBinding(
			key.WithKeys(" ", "x"),
			key.WithHelp("space/x", "toggle selection"),
		),
		Back: key.NewBinding(
			key.WithKeys("q", "esc"),
			key.WithHelp("q/esc", "go back"),
		),
		Help: key.NewBinding(
			key.WithKeys("?"),
			key.WithHelp("?", "toggle help"),
		),
	}
}

// ShortHelp returns keybindings for the short help view
func (k ToolKeyMap) ShortHelp() []key.Binding {
	return []key.Binding{k.Refresh, k.Install, k.Update, k.Sync, k.Back}
}

// FullHelp returns keybindings for the full help view
func (k ToolKeyMap) FullHelp() [][]key.Binding {
	return [][]key.Binding{
		{k.Install, k.Update, k.Remove},
		{k.Sync, k.Refresh, k.Select},
		{k.Back, k.Help},
	}
}

// NavigationKeyMap defines keybindings for navigation
type NavigationKeyMap struct {
	Up    key.Binding
	Down  key.Binding
	Enter key.Binding
	Tab   key.Binding
	Quit  key.Binding
}

// DefaultNavigationKeyMap returns the default navigation keybindings
func DefaultNavigationKeyMap() NavigationKeyMap {
	return NavigationKeyMap{
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
			key.WithHelp("enter", "select/confirm"),
		),
		Tab: key.NewBinding(
			key.WithKeys("tab"),
			key.WithHelp("tab", "next field"),
		),
		Quit: key.NewBinding(
			key.WithKeys("ctrl+c"),
			key.WithHelp("ctrl+c", "force quit"),
		),
	}
}