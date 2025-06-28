package screens

import (
	"context"
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/list"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/yourusername/dotfiles/internal/theme"
	"github.com/yourusername/dotfiles/internal/tools"
	"github.com/yourusername/dotfiles/internal/tui/components"
	"github.com/yourusername/dotfiles/internal/types"
)

// ToolScreen represents a tool-specific screen
type ToolScreen struct {
	tool         tools.Tool
	themeManager *theme.ThemeManager
	list         list.Model
	progress     components.ProgressComponent
	width        int
	height       int
	loading      bool
	error        error
}


// NewToolScreen creates a new tool screen
func NewToolScreen(tool tools.Tool, themeManager *theme.ThemeManager, width, height int) ToolScreen {
	return ToolScreen{
		tool:         tool,
		themeManager: themeManager,
		progress:     components.NewProgressComponent(width),
		width:        width,
		height:       height,
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
		switch msg.String() {
		case "r":
			ts.loading = true
			return ts, ts.loadToolStatus()
		case "i":
			if !ts.loading {
				return ts, ts.installSelected()
			}
		case "u":
			if !ts.loading {
				return ts, ts.updateSelected()
			}
		case "d":
			if !ts.loading {
				return ts, ts.removeSelected()
			}
		case "s":
			if !ts.loading {
				return ts, ts.syncAll()
			}
		}

		if !ts.loading {
			var cmd tea.Cmd
			ts.list, cmd = ts.list.Update(msg)
			cmds = append(cmds, cmd)
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
	var help []string
	
	if !ts.loading {
		help = append(help,
			"[r] refresh",
			"[i] install",
			"[u] update",
			"[d] remove",
			"[s] sync",
			"[↑/↓] navigate",
			"[q] back",
		)
	}

	styles := ts.themeManager.GetStyles()
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