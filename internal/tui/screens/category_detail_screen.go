package screens

import (
	"context"
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/list"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/yourusername/dotfiles/internal/theme"
	"github.com/yourusername/dotfiles/internal/tools"
	"github.com/yourusername/dotfiles/internal/common"
	"github.com/yourusername/dotfiles/internal/tui/components"
	"github.com/yourusername/dotfiles/internal/tui/keys"
	"github.com/yourusername/dotfiles/internal/types"
)


// CategoryDetailScreen represents a detailed view of packages within a category
type CategoryDetailScreen struct {
	category     string
	categoryTool tools.CategoryTool
	themeManager *theme.ThemeManager
	list         list.Model
	progress     components.ProgressComponent
	keys         keys.ToolKeyMap
	navKeys      keys.NavigationKeyMap
	width        int
	height       int
	loading      bool
	error        error
	showHelp     bool
}

// NewCategoryDetailScreen creates a new category detail screen
func NewCategoryDetailScreen(category string, tool tools.CategoryTool, themeManager *theme.ThemeManager, width, height int) CategoryDetailScreen {
	return CategoryDetailScreen{
		category:     category,
		categoryTool: tool,
		themeManager: themeManager,
		progress:     components.NewProgressComponent(width),
		keys:         keys.DefaultToolKeyMap(),
		navKeys:      keys.DefaultNavigationKeyMap(),
		width:        width,
		height:       height,
		showHelp:     false,
	}
}

// CategoryPackagesLoadedMsg represents loaded category packages
type CategoryPackagesLoadedMsg struct {
	Category string
	Packages []types.ToolItem
}

// CategoryPackageOperationCompleteMsg represents completed package operation
type CategoryPackageOperationCompleteMsg struct {
	Category  string
	Operation string
	Package   string
	Success   bool
	Error     error
	Result    *types.OperationResult
}

// Init initializes the category detail screen
func (cs CategoryDetailScreen) Init() tea.Cmd {
	return tea.Batch(
		cs.loadCategoryPackages(),
	)
}

// Update handles messages for the category detail screen
func (cs CategoryDetailScreen) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		cs.width = msg.Width
		cs.height = msg.Height
		
		h, v := lipgloss.NewStyle().Margin(2, 4).GetFrameSize()
		cs.list.SetSize(msg.Width-h, msg.Height-v-4) // Leave space for header and help
		
	case CategoryPackagesLoadedMsg:
		if msg.Category == cs.category {
			cs.loading = false
			cs.error = nil
			
			// Convert packages to list items
			items := make([]list.Item, len(msg.Packages))
			for i, pkg := range msg.Packages {
				items[i] = components.NewStatusItem(pkg)
			}
			
			// Create new list with items
			delegate := components.NewStatusListDelegate()
			cs.list = list.New(items, delegate, cs.width, cs.height-8)
			cs.list.Title = fmt.Sprintf("%s > %s Packages", 
				strings.Title(cs.categoryTool.Name()), 
				strings.Title(cs.category))
			cs.list.SetShowStatusBar(true)
			cs.list.SetFilteringEnabled(true)
			cs.list.Styles.Title = cs.themeManager.GetStyles().Header
		}
		
	case CategoryPackageOperationCompleteMsg:
		if msg.Category == cs.category {
			cs.loading = false
			if !msg.Success {
				cs.error = msg.Error
			} else {
				cs.error = nil
				// Reload packages to show updated status
				return cs, cs.loadCategoryPackages()
			}
		}
		
	case tea.KeyMsg:
		// Global navigation keys
		if key.Matches(msg, cs.keys.Back) {
			return cs, func() tea.Msg { return common.BackMsg{} }
		}
		
		if key.Matches(msg, cs.keys.Help) {
			cs.showHelp = !cs.showHelp
			return cs, nil
		}
		
		// Don't process other keys while loading
		if cs.loading {
			return cs, nil
		}
		
		// Package operations
		switch {
		case key.Matches(msg, cs.keys.Install):
			if selectedItem := cs.list.SelectedItem(); selectedItem != nil {
				if statusItem, ok := selectedItem.(components.StatusItem); ok {
					cs.loading = true
					return cs, cs.installPackage(statusItem.ToolItem().Name)
				}
			}
			
		case key.Matches(msg, cs.keys.Refresh):
			cs.loading = true
			return cs, cs.loadCategoryPackages()
			
		default:
			// Handle list navigation
			var cmd tea.Cmd
			cs.list, cmd = cs.list.Update(msg)
			cmds = append(cmds, cmd)
		}
	}
	
	// Update progress if loading
	if cs.loading {
		var cmd tea.Cmd
		cs.progress, cmd = cs.progress.Update(msg)
		cmds = append(cmds, cmd)
	}
	
	return cs, tea.Batch(cmds...)
}

// View renders the category detail screen
func (cs CategoryDetailScreen) View() string {
	if cs.loading && cs.list.Items() == nil {
		return cs.renderLoading()
	}
	
	if cs.error != nil {
		return cs.renderError()
	}
	
	if cs.showHelp {
		return cs.renderHelp()
	}
	
	return cs.renderMain()
}

// loadCategoryPackages loads packages for the current category
func (cs CategoryDetailScreen) loadCategoryPackages() tea.Cmd {
	return func() tea.Msg {
		packages, err := cs.categoryTool.ListCategoryItems(context.Background(), cs.category)
		if err != nil {
			return CategoryPackageOperationCompleteMsg{
				Category:  cs.category,
				Operation: "load",
				Success:   false,
				Error:     err,
			}
		}
		
		return CategoryPackagesLoadedMsg{
			Category: cs.category,
			Packages: packages,
		}
	}
}

// installPackage installs a specific package
func (cs CategoryDetailScreen) installPackage(packageName string) tea.Cmd {
	return func() tea.Msg {
		result, err := cs.categoryTool.InstallCategoryItem(context.Background(), cs.category, packageName)
		
		return CategoryPackageOperationCompleteMsg{
			Category:  cs.category,
			Operation: "install",
			Package:   packageName,
			Success:   err == nil && result.Success,
			Error:     err,
			Result:    result,
		}
	}
}

// renderMain renders the main category detail view
func (cs CategoryDetailScreen) renderMain() string {
	mainContent := cs.list.View()
	
	if cs.loading {
		progressView := cs.progress.View()
		mainContent = lipgloss.JoinVertical(lipgloss.Left, mainContent, progressView)
	}
	
	help := cs.renderHelpFooter()
	
	return lipgloss.JoinVertical(lipgloss.Left, mainContent, help)
}

// renderLoading renders the loading state
func (cs CategoryDetailScreen) renderLoading() string {
	title := cs.themeManager.GetStyles().Header.Render(
		fmt.Sprintf("Loading %s packages...", cs.category))
	
	progress := cs.progress.View()
	
	content := lipgloss.JoinVertical(lipgloss.Center,
		"",
		title,
		"",
		progress,
		"",
	)
	
	return lipgloss.Place(cs.width, cs.height,
		lipgloss.Center, lipgloss.Center, content)
}

// renderError renders the error state
func (cs CategoryDetailScreen) renderError() string {
	styles := cs.themeManager.GetStyles()
	
	title := styles.Header.Render("Error")
	errorMsg := styles.Error.Render(fmt.Sprintf("Failed to load %s packages:\n%v", cs.category, cs.error))
	
	help := styles.Help.Render("Press 'r' to retry, 'esc' to go back")
	
	content := lipgloss.JoinVertical(lipgloss.Center,
		"",
		title,
		"",
		errorMsg,
		"",
		help,
		"",
	)
	
	return lipgloss.Place(cs.width, cs.height,
		lipgloss.Center, lipgloss.Center, content)
}

// renderHelp renders the help screen
func (cs CategoryDetailScreen) renderHelp() string {
	styles := cs.themeManager.GetStyles()
	
	title := styles.Header.Render("Category Package Management - Help")
	
	keyBindings := []string{
		"Navigation:",
		"  ↑/k       - Move up",
		"  ↓/j       - Move down", 
		"  /         - Filter packages",
		"  esc       - Clear filter",
		"",
		"Package Operations:",
		"  i         - Install selected package",
		"  r         - Refresh package list",
		"",
		"General:",
		"  ?         - Toggle this help",
		"  esc/q     - Go back to tool screen",
	}
	
	helpText := styles.Help.Render(strings.Join(keyBindings, "\n"))
	
	content := lipgloss.JoinVertical(lipgloss.Left,
		"",
		title,
		"",
		helpText,
		"",
	)
	
	return lipgloss.Place(cs.width, cs.height,
		lipgloss.Center, lipgloss.Center, content)
}

// renderHelpFooter renders the help footer
func (cs CategoryDetailScreen) renderHelpFooter() string {
	styles := cs.themeManager.GetStyles()
	
	keys := []string{
		"i: install",
		"r: refresh", 
		"?: help",
		"esc: back",
	}
	
	if cs.list.FilterState() == list.Filtering {
		keys = []string{"esc: clear filter", "enter: apply filter"}
	}
	
	return styles.Help.Render(strings.Join(keys, " • "))
}