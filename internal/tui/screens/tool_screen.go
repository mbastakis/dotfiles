package screens

import (
	"context"
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/list"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/mbastakis/dotfiles/internal/theme"
	"github.com/mbastakis/dotfiles/internal/tools"
	"github.com/mbastakis/dotfiles/internal/common"
	"github.com/mbastakis/dotfiles/internal/tui/components"
	"github.com/mbastakis/dotfiles/internal/tui/keys"
	"github.com/mbastakis/dotfiles/internal/types"
)


// ToolScreen represents a tool-specific screen
type ToolScreen struct {
	tool         tools.Tool
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


// NewToolScreen creates a new tool screen
func NewToolScreen(tool tools.Tool, themeManager *theme.ThemeManager, width, height int) ToolScreen {
	return ToolScreen{
		tool:         tool,
		themeManager: themeManager,
		progress:     components.NewProgressComponent(width),
		keys:         keys.DefaultToolKeyMap(),
		navKeys:      keys.DefaultNavigationKeyMap(),
		width:        width,
		height:       height,
		showHelp:     false,
	}
}

// ToolStatusLoadedMsg represents loaded tool status
type ToolStatusLoadedMsg struct {
	Status *types.ToolStatus
	Error  error
}

// ToolOperationCompleteMsg represents a completed tool operation
type ToolOperationCompleteMsg struct {
	Result *types.OperationResult
	Error  error
}

// Init initializes the tool screen
func (ts ToolScreen) Init() tea.Cmd {
	return tea.Batch(
		ts.progress.Init(),
		ts.loadToolStatus(),
	)
}

// Update handles tool screen updates
func (ts ToolScreen) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		ts.width = msg.Width
		ts.height = msg.Height
		ts.list.SetSize(msg.Width-4, msg.Height-8) // Account for header/footer
		ts.progress = components.NewProgressComponent(msg.Width)

	case tea.KeyMsg:
		// Handle help toggle
		if key.Matches(msg, ts.keys.Help) {
			ts.showHelp = !ts.showHelp
			return ts, nil
		}

		// Handle back/quit
		if key.Matches(msg, ts.keys.Back) {
			// This will be handled by the parent AppModel
			return ts, nil
		}

		// Only process tool operations if not loading
		if !ts.loading {
			switch {
			case key.Matches(msg, ts.keys.Refresh):
				ts.loading = true
				return ts, ts.loadToolStatus()
			case key.Matches(msg, ts.keys.Install):
				if selectedItem := ts.list.SelectedItem(); selectedItem != nil {
					ts.loading = true
					return ts, ts.installSelected()
				}
			case key.Matches(msg, ts.keys.Update):
				if selectedItem := ts.list.SelectedItem(); selectedItem != nil {
					ts.loading = true
					return ts, ts.updateSelected()
				}
			case key.Matches(msg, ts.keys.Remove):
				if selectedItem := ts.list.SelectedItem(); selectedItem != nil {
					ts.loading = true
					return ts, ts.removeSelected()
				}
			case key.Matches(msg, ts.keys.Sync):
				ts.loading = true
				return ts, ts.syncAll()
			case key.Matches(msg, ts.keys.Select):
				// Toggle selection for batch operations (future enhancement)
				// For now, just move cursor
				var cmd tea.Cmd
				ts.list, cmd = ts.list.Update(msg)
				cmds = append(cmds, cmd)
			case key.Matches(msg, ts.navKeys.Enter):
				// Handle Enter key for category navigation (homebrew only)
				if categoryTool, ok := ts.tool.(tools.CategoryTool); ok && categoryTool.SupportsCategories() {
					if selectedItem := ts.list.SelectedItem(); selectedItem != nil {
						if statusItem, ok := selectedItem.(components.StatusItem); ok {
							// Navigate to category detail screen
							categoryScreen := NewCategoryDetailScreen(
								statusItem.ToolItem().Name, 
								categoryTool, 
								ts.themeManager, 
								ts.width, 
								ts.height)
							return ts, func() tea.Msg {
								return common.NavigateMsg{Screen: categoryScreen}
							}
						}
					}
				}
				// If not a category tool, handle as normal list navigation
				var cmd tea.Cmd
				ts.list, cmd = ts.list.Update(msg)
				cmds = append(cmds, cmd)
			default:
				// Handle navigation keys (up/down/enter)
				// Don't process Enter key here for tool operations
				// It should only be used for navigation in lists
				var cmd tea.Cmd
				ts.list, cmd = ts.list.Update(msg)
				cmds = append(cmds, cmd)
			}
		}

	case ToolStatusLoadedMsg:
		ts.loading = false
		ts.error = msg.Error
		if msg.Status != nil {
			ts.list = components.CreateStatusList(msg.Status.Items, ts.width-4, ts.height-8)
		}

	case ToolOperationCompleteMsg:
		ts.loading = false
		if msg.Error != nil {
			ts.error = msg.Error
		} else {
			// Reload status after operation
			return ts, ts.loadToolStatus()
		}

	default:
		var cmd tea.Cmd
		ts.progress, cmd = ts.progress.Update(msg)
		cmds = append(cmds, cmd)
	}

	return ts, tea.Batch(cmds...)
}

// View renders the tool screen
func (ts ToolScreen) View() string {
	var sections []string

	// Header
	header := ts.renderHeader()
	sections = append(sections, header)

	// Main content
	if ts.loading {
		content := ts.progress.View()
		sections = append(sections, content)
	} else if ts.error != nil {
		styles := ts.themeManager.GetStyles()
		content := styles.Error.Render(fmt.Sprintf("Error: %v", ts.error))
		sections = append(sections, content)
	} else {
		content := ts.list.View()
		sections = append(sections, content)
	}

	// Footer
	footer := ts.renderFooter()
	sections = append(sections, footer)

	return lipgloss.JoinVertical(lipgloss.Left, sections...)
}

func (ts ToolScreen) renderHeader() string {
	styles := ts.themeManager.GetStyles()
	title := fmt.Sprintf("%s Tool Management", strings.Title(ts.tool.Name()))
	
	var status string
	if ts.tool.IsEnabled() {
		status = styles.Healthy.Render("● Enabled")
	} else {
		status = styles.Disabled.Render("● Disabled")
	}

	headerContent := fmt.Sprintf("%s %s", title, status)
	return styles.Header.Width(ts.width - 2).Render(headerContent)
}

func (ts ToolScreen) renderFooter() string {
	styles := ts.themeManager.GetStyles()
	
	if ts.showHelp {
		// Show full help
		var helpItems []string
		for _, row := range ts.keys.FullHelp() {
			for _, binding := range row {
				helpItems = append(helpItems, fmt.Sprintf("[%s] %s", binding.Help().Key, binding.Help().Desc))
			}
		}
		helpText := styles.Help.Render(strings.Join(helpItems, " • "))
		return styles.Footer.Width(ts.width - 2).Render(helpText)
	}
	
	// Show contextual help based on state
	var help []string
	
	if ts.loading {
		help = append(help, "Loading...")
	} else {
		// Show available operations
		if ts.list.SelectedItem() != nil {
			help = append(help,
				fmt.Sprintf("[%s] %s", ts.keys.Install.Help().Key, ts.keys.Install.Help().Desc),
				fmt.Sprintf("[%s] %s", ts.keys.Update.Help().Key, ts.keys.Update.Help().Desc),
				fmt.Sprintf("[%s] %s", ts.keys.Remove.Help().Key, ts.keys.Remove.Help().Desc),
			)
		}
		help = append(help,
			fmt.Sprintf("[%s] %s", ts.keys.Sync.Help().Key, ts.keys.Sync.Help().Desc),
			fmt.Sprintf("[%s] %s", ts.keys.Refresh.Help().Key, ts.keys.Refresh.Help().Desc),
			"[↑/↓] navigate",
			fmt.Sprintf("[%s] back", ts.keys.Back.Help().Key),
		)
		
		if !ts.showHelp {
			help = append(help, fmt.Sprintf("[%s] more help", ts.keys.Help.Help().Key))
		}
	}

	helpText := styles.Help.Render(strings.Join(help, " • "))
	return styles.Footer.Width(ts.width - 2).Render(helpText)
}

func (ts ToolScreen) loadToolStatus() tea.Cmd {
	return func() tea.Msg {
		ctx := context.Background()
		status, err := ts.tool.Status(ctx)
		return ToolStatusLoadedMsg{Status: status, Error: err}
	}
}

func (ts ToolScreen) installSelected() tea.Cmd {
	return func() tea.Msg {
		ctx := context.Background()
		
		// Get selected items
		var items []string
		if selectedItem, ok := ts.list.SelectedItem().(components.StatusItem); ok {
			// For now, just operate on the selected item
			// In a more advanced implementation, we'd support multi-selection
			items = []string{selectedItem.Title()}
		}

		result, err := ts.tool.Install(ctx, items)
		return ToolOperationCompleteMsg{Result: result, Error: err}
	}
}

func (ts ToolScreen) updateSelected() tea.Cmd {
	return func() tea.Msg {
		ctx := context.Background()
		
		var items []string
		if selectedItem, ok := ts.list.SelectedItem().(components.StatusItem); ok {
			items = []string{selectedItem.Title()}
		}

		result, err := ts.tool.Update(ctx, items)
		return ToolOperationCompleteMsg{Result: result, Error: err}
	}
}

func (ts ToolScreen) removeSelected() tea.Cmd {
	return func() tea.Msg {
		ctx := context.Background()
		
		var items []string
		if selectedItem, ok := ts.list.SelectedItem().(components.StatusItem); ok {
			items = []string{selectedItem.Title()}
		}

		result, err := ts.tool.Remove(ctx, items)
		return ToolOperationCompleteMsg{Result: result, Error: err}
	}
}

func (ts ToolScreen) syncAll() tea.Cmd {
	return func() tea.Msg {
		ctx := context.Background()
		result, err := ts.tool.Sync(ctx)
		return ToolOperationCompleteMsg{Result: result, Error: err}
	}
}