package tui

import (
	tea "github.com/charmbracelet/bubbletea"
	"github.com/yourusername/dotfiles/internal/config"
	"github.com/yourusername/dotfiles/internal/tools"
	"github.com/yourusername/dotfiles/internal/tui/models"
)

// RunTUI starts the TUI application
func RunTUI(config *config.Config, registry *tools.ToolRegistry) error {
	model := models.NewAppModel(config, registry)
	p := tea.NewProgram(model, tea.WithAltScreen())
	_, err := p.Run()
	return err
}

// newMainModel creates the main TUI model (legacy function)
func newMainModel(cfg *config.Config, registry *tools.ToolRegistry) models.MainModel {
	return models.NewMainModel(cfg, registry)
}