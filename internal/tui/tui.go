package tui

import (
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/yourusername/dotfiles/internal/config"
	"github.com/yourusername/dotfiles/internal/tools"
)

// TUI represents the main TUI application
type TUI struct {
	config   *config.Config
	registry *tools.ToolRegistry
	program  *tea.Program
}

// NewTUI creates a new TUI instance
func NewTUI(cfg *config.Config, registry *tools.ToolRegistry) *TUI {
	return &TUI{
		config:   cfg,
		registry: registry,
	}
}

// Run starts the TUI application
func (t *TUI) Run() error {
	model := newMainModel(t.config, t.registry)
	t.program = tea.NewProgram(model, tea.WithAltScreen())
	
	_, err := t.program.Run()
	return err
}

// Styles
var (
	titleStyle = lipgloss.NewStyle().
		Foreground(lipgloss.Color("#FFFDF5")).
		Background(lipgloss.Color("#25A065")).
		Padding(0, 1).
		Bold(true)

	subtitleStyle = lipgloss.NewStyle().
		Foreground(lipgloss.Color("#FFFDF5")).
		Background(lipgloss.Color("#3C3C3C")).
		Padding(0, 1)

	statusStyle = lipgloss.NewStyle().
		Foreground(lipgloss.Color("#FFFF00")).
		Italic(true)

	helpStyle = lipgloss.NewStyle().
		Foreground(lipgloss.Color("#626262"))

	boxStyle = lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("62")).
		Padding(1, 2)

	activeBoxStyle = lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#25A065")).
		Padding(1, 2)
)