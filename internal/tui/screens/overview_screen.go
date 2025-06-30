package screens

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/table"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/perf"
	"github.com/mbastakis/dotfiles/internal/theme"
	"github.com/mbastakis/dotfiles/internal/tools"
	"github.com/mbastakis/dotfiles/internal/tui/keys"
	"github.com/mbastakis/dotfiles/internal/types"
)

// OverviewScreen shows a comprehensive overview of all tools
type OverviewScreen struct {
	config       *config.Config
	registry     *tools.ToolRegistry
	themeManager *theme.ThemeManager
	table        table.Model
	keys         keys.ToolKeyMap
	navKeys      keys.NavigationKeyMap
	width        int
	height       int
	loading      bool
	lastUpdate   time.Time
	statuses     map[string]*types.ToolStatus // Store loaded statuses
}


// SystemStatusMsg contains loaded system status
type SystemStatusMsg struct {
	Statuses map[string]*types.ToolStatus
	Error    error
}

// NewOverviewScreen creates a new overview screen
func NewOverviewScreen(cfg *config.Config, registry *tools.ToolRegistry, themeManager *theme.ThemeManager, width, height int) OverviewScreen {
	// Create table columns with more detailed information
	columns := []table.Column{
		{Title: "Tool", Width: 12},
		{Title: "Status", Width: 10},
		{Title: "Items", Width: 8},
		{Title: "Installed", Width: 10},
		{Title: "Categories", Width: 12},
		{Title: "Versions", Width: 10},
		{Title: "Last Update", Width: 10},
		{Title: "Description", Width: 20},
	}

	// Create initial placeholder rows to show all tools
	var initialRows []table.Row
	for _, tool := range registry.List() {
		initialRows = append(initialRows, table.Row{
			strings.Title(tool.Name()),
			"Loading...",
			"-",
			"-",
			"-",
			"-",
			"-",
			"Checking status...",
		})
	}

	t := table.New(
		table.WithColumns(columns),
		table.WithRows(initialRows),
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
		keys:         keys.DefaultToolKeyMap(),
		navKeys:      keys.DefaultNavigationKeyMap(),
		width:        width,
		height:       height,
		statuses:     make(map[string]*types.ToolStatus),
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
		// Handle back/quit - let parent handle navigation
		if key.Matches(msg, os.keys.Back) {
			return os, nil
		}

		// Handle refresh
		if key.Matches(msg, os.keys.Refresh) {
			os.loading = true
			return os, os.loadSystemStatus()
		}

		// Forward to table for navigation
		os.table, cmd = os.table.Update(msg)

	case SystemStatusMsg:
		os.loading = false
		os.lastUpdate = time.Now()
		if msg.Error == nil {
			os.statuses = msg.Statuses
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

	// Debug: Simple view to check if navigation works
	if os.width == 0 || os.height == 0 {
		return "Initializing overview screen..."
	}

	var sections []string

	// Header
	header := os.renderHeader()
	sections = append(sections, header)

	// Summary stats - make this simpler for debugging
	summary := os.renderSummary()
	sections = append(sections, summary)

	// Table - ensure it has proper height
	tableHeight := os.height - 15 // Reserve space for header/footer
	if tableHeight < 5 {
		tableHeight = 5
	}
	os.table.SetHeight(tableHeight)
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
	errorCount := 0
	totalItems := 0
	installedItems := 0

	// Calculate actual statistics from loaded status data
	for _, tool := range tools {
		if status, exists := os.statuses[tool.Name()]; exists {
			if status.Enabled && status.Healthy {
				healthyCount++
			}
			if status.Error != nil {
				errorCount++
			}
			for _, item := range status.Items {
				totalItems++
				if item.Installed {
					installedItems++
				}
			}
		}
	}

	var sections []string

	// Main tools summary
	toolsSummary := fmt.Sprintf(
		"📊 Tools: %d total • %d enabled • %d healthy",
		len(tools), enabledCount, healthyCount,
	)
	if errorCount > 0 {
		toolsSummary += fmt.Sprintf(" • %d errors", errorCount)
	}
	sections = append(sections, styles.Subtitle.Render(toolsSummary))

	// Items summary if we have data
	if totalItems > 0 {
		itemsSummary := fmt.Sprintf(
			"📦 Items: %d total • %d installed",
			totalItems, installedItems,
		)
		sections = append(sections, styles.Help.Render(itemsSummary))
	}

	// Performance metrics
	monitor := perf.GetGlobalMonitor()
	if monitor != nil {
		memStats := monitor.GetCurrentMemoryStats()
		perfMetrics := monitor.GetPerformanceMetrics()
		
		if !memStats.Timestamp.IsZero() {
			// Memory usage
			perfSummary := fmt.Sprintf(
				"⚡ Performance: %s memory • %d goroutines • %d GC cycles",
				formatBytes(memStats.Alloc),
				memStats.NumGoroutine,
				memStats.NumGC,
			)
			sections = append(sections, styles.Help.Render(perfSummary))

			// Cache statistics if available
			if len(perfMetrics.CacheHitRatio) > 0 {
				var cacheStrs []string
				for cacheName, ratio := range perfMetrics.CacheHitRatio {
					cacheStrs = append(cacheStrs, fmt.Sprintf("%s: %.1f%%", cacheName, ratio*100))
				}
				if len(cacheStrs) > 0 {
					cacheInfo := fmt.Sprintf("📊 Cache: %s", strings.Join(cacheStrs, ", "))
					sections = append(sections, styles.Help.Render(cacheInfo))
				}
			}

			// Operation statistics if available
			if len(perfMetrics.OperationCounts) > 0 {
				totalOps := int64(0)
				for _, count := range perfMetrics.OperationCounts {
					totalOps += count
				}
				if totalOps > 0 {
					opsInfo := fmt.Sprintf("🔄 Operations: %d total", totalOps)
					sections = append(sections, styles.Help.Render(opsInfo))
				}
			}
		}
	}

	// System information
	systemInfo := fmt.Sprintf(
		"🏠 Dotfiles: %s • Theme: %s",
		os.config.Global.DotfilesPath,
		os.config.TUI.ColorScheme,
	)
	sections = append(sections, styles.Help.Render(systemInfo))

	// Additional system details
	if !os.lastUpdate.IsZero() {
		updateInfo := fmt.Sprintf(
			"🕒 Last sync: %s • Backup: %t • Dry run: %t",
			os.lastUpdate.Format("15:04:05"),
			os.config.Global.BackupEnabled,
			os.config.Global.DryRun,
		)
		sections = append(sections, styles.Help.Render(updateInfo))
	}

	return lipgloss.JoinVertical(lipgloss.Left, sections...)
}

func (os OverviewScreen) renderErrorPanel() string {
	styles := os.themeManager.GetStyles()
	var errors []string

	// Collect errors from tool statuses
	for _, tool := range os.registry.List() {
		if status, exists := os.statuses[tool.Name()]; exists {
			if status.Error != nil {
				errors = append(errors, fmt.Sprintf("❌ %s: %s", tool.Name(), status.Error.Error()))
			}
			// Also check for item-level errors
			for _, item := range status.Items {
				if item.Error != "" {
					errors = append(errors, fmt.Sprintf("⚠️  %s/%s: %s", tool.Name(), item.Name, item.Error))
				}
			}
		}
	}

	if len(errors) == 0 {
		return ""
	}

	// Limit the number of errors shown to prevent overwhelming display
	maxErrors := 5
	if len(errors) > maxErrors {
		errors = errors[:maxErrors]
		errors = append(errors, fmt.Sprintf("... and %d more errors", len(errors)-maxErrors))
	}

	errorContent := strings.Join(errors, "\n")
	
	// Style the error panel with a border
	errorStyle := styles.Error.Copy().
		BorderStyle(lipgloss.RoundedBorder()).
		BorderForeground(styles.Error.GetForeground()).
		Padding(0, 1).
		Margin(0, 0, 1, 0).
		Width(os.width - 4)

	return errorStyle.Render("🚨 Issues Found:\n" + errorContent)
}

func (os OverviewScreen) renderCategoryPanel() string {
	styles := os.themeManager.GetStyles()
	var categoryData []string

	// Check for tools that support categories
	for _, tool := range os.registry.List() {
		if categoryTool, ok := tool.(tools.CategoryTool); ok && categoryTool.SupportsCategories() {
			if status, exists := os.statuses[tool.Name()]; exists && status.Enabled {
				categories := make(map[string][]string)
				
				// Group items by category
				for _, item := range status.Items {
					if item.Category != "" {
						statusIcon := "❌"
						if item.Installed {
							statusIcon = "✅"
						} else if item.Enabled {
							statusIcon = "⏳"
						}
						categories[item.Category] = append(categories[item.Category], fmt.Sprintf("%s %s", statusIcon, item.Name))
					}
				}

				// Format category data for this tool
				if len(categories) > 0 {
					toolInfo := fmt.Sprintf("📦 %s:", strings.Title(tool.Name()))
					categoryData = append(categoryData, toolInfo)
					
					for catName, items := range categories {
						// Limit items shown per category to prevent overwhelming display
						maxItems := 3
						displayItems := items
						if len(items) > maxItems {
							displayItems = items[:maxItems]
							displayItems = append(displayItems, fmt.Sprintf("... and %d more", len(items)-maxItems))
						}
						
						catInfo := fmt.Sprintf("  • %s: %s", catName, strings.Join(displayItems, ", "))
						categoryData = append(categoryData, catInfo)
					}
				}
			}
		}
	}

	if len(categoryData) == 0 {
		return ""
	}

	categoryContent := strings.Join(categoryData, "\n")
	
	// Style the category panel with a border
	categoryStyle := styles.Subtitle.Copy().
		BorderStyle(lipgloss.RoundedBorder()).
		BorderForeground(styles.Subtitle.GetForeground()).
		Padding(0, 1).
		Margin(0, 0, 1, 0).
		Width(os.width - 4)

	return categoryStyle.Render("📊 Category Breakdown:\n" + categoryContent)
}

func (os OverviewScreen) renderFooter() string {
	styles := os.themeManager.GetStyles()
	
	var help []string
	if !os.loading {
		help = append(help,
			fmt.Sprintf("[%s] %s", os.keys.Refresh.Help().Key, os.keys.Refresh.Help().Desc),
			"[↑/↓] navigate",
			fmt.Sprintf("[%s] back", os.keys.Back.Help().Key),
		)
	} else {
		help = append(help, "Loading...")
	}
	
	helpText := styles.Help.Render(strings.Join(help, " • "))
	return styles.Footer.Width(os.width - 2).Render(helpText)
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
				"-",
				"-",
				"Status not available",
			})
			continue
		}

		// Calculate statistics
		totalItems := len(status.Items)
		installedItems := 0
		categories := make(map[string]int)
		versions := make(map[string]int)

		for _, item := range status.Items {
			if item.Installed {
				installedItems++
			}
			if item.Category != "" {
				categories[item.Category]++
			}
			if item.Version != "" {
				versions[item.Version]++
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
		if status.Error != nil {
			statusText = "💥 Error"
		}

		// Categories summary
		categoriesText := "-"
		if len(categories) > 0 {
			var catStrs []string
			for cat, count := range categories {
				catStrs = append(catStrs, fmt.Sprintf("%s(%d)", cat, count))
			}
			categoriesText = strings.Join(catStrs, ", ")
			// Truncate if too long
			if len(categoriesText) > 10 {
				categoriesText = categoriesText[:10] + "..."
			}
		}

		// Versions summary
		versionsText := "-"
		if len(versions) > 0 {
			var verStrs []string
			for ver, count := range versions {
				if count > 1 {
					verStrs = append(verStrs, fmt.Sprintf("%s(%d)", ver, count))
				} else {
					verStrs = append(verStrs, ver)
				}
			}
			versionsText = strings.Join(verStrs, ", ")
			// Truncate if too long
			if len(versionsText) > 8 {
				versionsText = versionsText[:8] + "..."
			}
		}

		// Last update time
		lastUpdateText := "-"
		if !status.LastCheck.IsZero() {
			if time.Since(status.LastCheck) < time.Hour {
				lastUpdateText = fmt.Sprintf("%dm ago", int(time.Since(status.LastCheck).Minutes()))
			} else if time.Since(status.LastCheck) < 24*time.Hour {
				lastUpdateText = fmt.Sprintf("%dh ago", int(time.Since(status.LastCheck).Hours()))
			} else {
				lastUpdateText = status.LastCheck.Format("Jan 2")
			}
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
			fmt.Sprintf("%d", installedItems),
			categoriesText,
			versionsText,
			lastUpdateText,
			description,
		})
	}

	os.table.SetRows(rows)
}

func (os OverviewScreen) loadSystemStatus() tea.Cmd {
	return func() tea.Msg {
		// Create context with overall timeout
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
		defer cancel()
		
		statuses := make(map[string]*types.ToolStatus)
		
		// Process each tool with individual timeout
		for _, tool := range os.registry.List() {
			// Create individual context with shorter timeout for each tool
			toolCtx, toolCancel := context.WithTimeout(ctx, 3*time.Second)
			
			// Channel to receive the result
			resultChan := make(chan *types.ToolStatus, 1)
			errorChan := make(chan error, 1)
			
			// Run tool status check in goroutine
			go func(t tools.Tool) {
				defer toolCancel()
				status, err := t.Status(toolCtx)
				if err != nil {
					errorChan <- err
				} else {
					resultChan <- status
				}
			}(tool)
			
			// Wait for result or timeout
			select {
			case status := <-resultChan:
				statuses[tool.Name()] = status
			case err := <-errorChan:
				// Create error status
				statuses[tool.Name()] = &types.ToolStatus{
					Name:      tool.Name(),
					Enabled:   true,
					Healthy:   false,
					Error:     err,
					Items:     []types.ToolItem{},
					LastCheck: time.Now(),
				}
			case <-toolCtx.Done():
				// Timeout - create timeout status
				statuses[tool.Name()] = &types.ToolStatus{
					Name:      tool.Name(),
					Enabled:   true,
					Healthy:   false,
					Error:     fmt.Errorf("status check timed out after 3 seconds"),
					Items:     []types.ToolItem{},
					LastCheck: time.Now(),
				}
			}
			
			toolCancel() // Clean up
		}

		return SystemStatusMsg{
			Statuses: statuses,
			Error:    nil,
		}
	}
}

// formatBytes formats bytes into human-readable format
func formatBytes(bytes uint64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := uint64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(bytes)/float64(div), "KMGTPE"[exp])
}
