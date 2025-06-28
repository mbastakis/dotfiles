package tui

import (
	tea "github.com/charmbracelet/bubbletea"
	"github.com/yourusername/dotfiles/internal/config"
	"github.com/yourusername/dotfiles/internal/theme"
	"github.com/yourusername/dotfiles/internal/tools"
	"github.com/yourusername/dotfiles/internal/tui/models"
)

// RunTUI starts the TUI application
func RunTUI(config *config.Config, registry *tools.ToolRegistry) error {
	// Initialize theme manager
	themeManager := theme.NewThemeManager(config.Global.DotfilesPath)
	themeManager.LoadThemes()
	
	// Set theme from config
	if config.TUI.ColorScheme != "" {
		themeManager.SetCurrentTheme(config.TUI.ColorScheme)
	}
	
	model := models.NewAppModel(config, registry, themeManager)
	p := tea.NewProgram(model, tea.WithAltScreen())
	_, err := p.Run()
	return err
}

// newMainModel creates the main TUI model (legacy function)
func newMainModel(cfg *config.Config, registry *tools.ToolRegistry) models.MainModel {
	themeManager := theme.NewThemeManager(cfg.Global.DotfilesPath)
	themeManager.LoadThemes()
	return models.NewMainModel(cfg, registry, themeManager)
}