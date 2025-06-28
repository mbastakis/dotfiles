package tui

import (
	"github.com/yourusername/dotfiles/internal/config"
	"github.com/yourusername/dotfiles/internal/tools"
	"github.com/yourusername/dotfiles/internal/tui/models"
)

// newMainModel creates the main TUI model
func newMainModel(cfg *config.Config, registry *tools.ToolRegistry) models.MainModel {
	return models.NewMainModel(cfg, registry)
}