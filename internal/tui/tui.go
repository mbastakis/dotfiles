package tui

import (
	tea "github.com/charmbracelet/bubbletea"
	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/theme"
	"github.com/mbastakis/dotfiles/internal/tools"
	"github.com/mbastakis/dotfiles/internal/tui/models"
)

// TUI represents the main TUI application
type TUI struct {
	config       *config.Config
	registry     *tools.ToolRegistry
	themeManager *theme.ThemeManager
	program      *tea.Program
}

// NewTUI creates a new TUI instance
func NewTUI(cfg *config.Config, registry *tools.ToolRegistry) *TUI {
	// Initialize theme manager
	themeManager := theme.NewThemeManager(cfg.Global.DotfilesPath)
	themeManager.LoadThemes()

	// Set theme from config
	if cfg.TUI.ColorScheme != "" {
		themeManager.SetCurrentTheme(cfg.TUI.ColorScheme)
	}

	return &TUI{
		config:       cfg,
		registry:     registry,
		themeManager: themeManager,
	}
}

// Run starts the TUI application
func (t *TUI) Run() error {
	model := models.NewAppModel(t.config, t.registry, t.themeManager)
	t.program = tea.NewProgram(model, tea.WithAltScreen())

	_, err := t.program.Run()
	return err
}
