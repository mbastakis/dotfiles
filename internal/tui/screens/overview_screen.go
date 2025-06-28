package screens

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/table"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/yourusername/dotfiles/internal/config"
	"github.com/yourusername/dotfiles/internal/theme"
	"github.com/yourusername/dotfiles/internal/tools"
	"github.com/yourusername/dotfiles/internal/types"
)

// OverviewScreen shows a comprehensive overview of all tools
type OverviewScreen struct {
	config       *config.Config
	registry     *tools.ToolRegistry
	themeManager *theme.ThemeManager
	table        table.Model
	width        int
	height       int
	loading      bool
	lastUpdate   time.Time
}


// SystemStatusMsg contains loaded system status
type SystemStatusMsg struct {
	Statuses map[string]*types.ToolStatus
	Error    error
}

// NewOverviewScreen creates a new overview screen
func NewOverviewScreen(cfg *config.Config, registry *tools.ToolRegistry, themeManager *theme.ThemeManager, width, height int) OverviewScreen {
	// Create table columns
	columns := []table.Column{
		{Title: "Tool", Width: 12},
		{Title: "Status", Width: 10},
		{Title: "Items", Width: 8},
		{Title: "Enabled", Width: 8},
		{Title: "Installed", Width: 10},
		{Title: "Description", Width: 30},
	}

	t := table.New(
		table.WithColumns(columns),
		table.WithFocused(true),
		table.WithHeight(height-10),
	)

	// Get theme styles and apply to table
	styles := themeManager.GetStyles()
	s := table.DefaultStyles()
	s.Header = styles.Header
	s.Selected = styles.ActiveButton
	t.SetStyles(s)

	return OverviewScreen{
		config:       cfg,
		registry:     registry,
		themeManager: themeManager,
		table:        t,
		width:        width,
		height:       height,
	}
}

// Init initializes the overview screen
func (os OverviewScreen) Init() tea.Cmd {
	return os.loadSystemStatus()
}

// Update handles overview screen updates
func (os OverviewScreen) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		os.width = msg.Width
		os.height = msg.Height
		os.table.SetWidth(msg.Width - 4)
		os.table.SetHeight(msg.Height - 10)

	case tea.KeyMsg:
		switch msg.String() {
		case "r":
			os.loading = true
			return os, os.loadSystemStatus()
		case "q", "esc":
			return os, tea.Quit
		}

		// Forward to table for navigation
		os.table, cmd = os.table.Update(msg)

	case SystemStatusMsg:
		os.loading = false
		os.lastUpdate = time.Now()
		if msg.Error == nil {
			os.updateTableData(msg.Statuses)
		}
	}

	return os, cmd
}

// View renders the overview screen
func (os OverviewScreen) View() string {
	if os.loading {
		return os.renderLoading()
	}

	var sections []string

	// Header
	header := os.renderHeader()
	sections = append(sections, header)

	// Summary stats
	summary := os.renderSummary()
	sections = append(sections, summary)

	// Table
	tableView := os.table.View()
	sections = append(sections, tableView)

	// Footer with help
	footer := os.renderFooter()
	sections = append(sections, footer)

	return lipgloss.JoinVertical(lipgloss.Left, sections...)
}

func (os OverviewScreen) renderHeader() string {
	styles := os.themeManager.GetStyles()
	title := "🏠 System Overview"
	timestamp := ""
	if !os.lastUpdate.IsZero() {
		timestamp = fmt.Sprintf("Last updated: %s", os.lastUpdate.Format("15:04:05"))
	}
	headerContent := lipgloss.JoinHorizontal(
		lipgloss.Left,
		styles.Title.Render(title),
		styles.Help.Render(" "+timestamp),
	)
	return styles.Header.Width(os.width-2).Render(headerContent)
}

func (os OverviewScreen) renderSummary() string {
	styles := os.themeManager.GetStyles()
	tools := os.registry.List()
	enabledCount := len(os.registry.ListEnabled())
	healthyCount := 0

	// This would need to be calculated from actual status data
	// For now, we'll show the counts we know
	summaryText := fmt.Sprintf(
		"📊 Tools: %d total • %d enabled • %d healthy",
		len(tools), enabledCount, healthyCount,
	)

	return styles.Subtitle.Render(summaryText)
}

func (os OverviewScreen) renderFooter() string {
	styles := os.themeManager.GetStyles()
	help := []string{
		"[r] refresh",
		"[↑/↓] navigate",
		"[q/esc] back",
	}
	return styles.Help.Render(strings.Join(help, " • "))
}

func (os OverviewScreen) renderLoading() string {
	return lipgloss.Place(
		os.width, os.height,
		lipgloss.Center, lipgloss.Center,
		"🔄 Loading system status...",
	)
}

func (os OverviewScreen) updateTableData(statuses map[string]*types.ToolStatus) {
	var rows []table.Row

	for _, tool := range os.registry.List() {
		status := statuses[tool.Name()]
		if status == nil {
			// Tool status not loaded
			rows = append(rows, table.Row{
				tool.Name(),
				"Unknown",
				"-",
				"-",
				"-",
				"Status not available",
			})
			continue
		}

		// Calculate statistics
		totalItems := len(status.Items)
		enabledItems := 0
		installedItems := 0

		for _, item := range status.Items {
			if item.Enabled {
				enabledItems++
			}
			if item.Installed {
				installedItems++
			}
		}

		// Status indicator
		statusText := "❌ Unhealthy"
		if status.Healthy {
			statusText = "✅ Healthy"
		}
		if !status.Enabled {
			statusText = "⏸️ Disabled"
		}

		// Tool description
		description := fmt.Sprintf("%s tool", strings.Title(tool.Name()))
		switch tool.Name() {
		case "stow":
			description = "GNU Stow package management"
		case "homebrew":
			description = "macOS package manager"
		case "npm":
			description = "Node.js package manager"
		case "uv":
			description = "Python tool installer"
		case "rsync":
			description = "File synchronization"
		case "apps":
			description = "Custom application scripts"
		}

		rows = append(rows, table.Row{
			strings.Title(tool.Name()),
			statusText,
			fmt.Sprintf("%d", totalItems),
			fmt.Sprintf("%d", enabledItems),
			fmt.Sprintf("%d", installedItems),
			description,
		})
	}

	os.table.SetRows(rows)
}

func (os OverviewScreen) loadSystemStatus() tea.Cmd {
	return func() tea.Msg {
		ctx := context.Background()
		statuses := make(map[string]*types.ToolStatus)

		for _, tool := range os.registry.List() {
			status, err := tool.Status(ctx)
			if err != nil {
				// Log error but continue with other tools
				continue
			}
			statuses[tool.Name()] = status
		}

		return SystemStatusMsg{
			Statuses: statuses,
			Error:    nil,
		}
	}
}
