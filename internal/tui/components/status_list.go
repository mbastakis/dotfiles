package components

import (
	"fmt"
	"io"

	"github.com/charmbracelet/bubbles/list"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/yourusername/dotfiles/internal/types"
)

// StatusItem represents a status item in the list
type StatusItem struct {
	toolItem types.ToolItem
}

// NewStatusItem creates a new StatusItem
func NewStatusItem(item types.ToolItem) StatusItem {
	return StatusItem{toolItem: item}
}

// ToolItem returns the underlying tool item
func (s StatusItem) ToolItem() types.ToolItem {
	return s.toolItem
}

// FilterValue implements list.Item interface
func (s StatusItem) FilterValue() string {
	return s.toolItem.Name
}

// Title returns the item title
func (s StatusItem) Title() string {
	return s.toolItem.Name
}

// Description returns the item description with status
func (s StatusItem) Description() string {
	status := s.getStatusIcon()
	desc := s.toolItem.Description
	if s.toolItem.Version != "" {
		desc = fmt.Sprintf("%s (v%s)", desc, s.toolItem.Version)
	}
	return fmt.Sprintf("%s %s", status, desc)
}

func (s StatusItem) getStatusIcon() string {
	if !s.toolItem.Enabled {
		return "⏸️"
	}

	switch s.toolItem.Status {
	case "installed", "linked", "synced", "ready":
		return "✅"
	case "not_installed", "not_linked", "needs_sync":
		return "❌"
	case "update_available", "partial":
		return "🔄"
	case "error":
		return "⚠️"
	case "disabled":
		return "⏸️"
	default:
		return "❓"
	}
}

// StatusListDelegate handles rendering of status items
type StatusListDelegate struct {
	styles StatusListStyles
}

type StatusListStyles struct {
	SelectedTitle    lipgloss.Style
	SelectedDesc     lipgloss.Style
	NormalTitle      lipgloss.Style
	NormalDesc       lipgloss.Style
	DimmedTitle      lipgloss.Style
	DimmedDesc       lipgloss.Style
}

func NewStatusListDelegate() StatusListDelegate {
	return StatusListDelegate{
		styles: StatusListStyles{
			SelectedTitle: lipgloss.NewStyle().
				Foreground(lipgloss.Color("170")).
				Bold(true),
			SelectedDesc: lipgloss.NewStyle().
				Foreground(lipgloss.Color("243")),
			NormalTitle: lipgloss.NewStyle().
				Foreground(lipgloss.Color("255")),
			NormalDesc: lipgloss.NewStyle().
				Foreground(lipgloss.Color("246")),
			DimmedTitle: lipgloss.NewStyle().
				Foreground(lipgloss.Color("240")),
			DimmedDesc: lipgloss.NewStyle().
				Foreground(lipgloss.Color("238")),
		},
	}
}

func (d StatusListDelegate) Height() int                               { return 2 }
func (d StatusListDelegate) Spacing() int                             { return 1 }
func (d StatusListDelegate) Update(msg tea.Msg, m *list.Model) tea.Cmd { return nil }

func (d StatusListDelegate) Render(w io.Writer, m list.Model, index int, item list.Item) {
	statusItem, ok := item.(StatusItem)
	if !ok {
		return
	}

	isSelected := index == m.Index()
	
	var titleStyle, descStyle lipgloss.Style
	if !statusItem.toolItem.Enabled {
		titleStyle = d.styles.DimmedTitle
		descStyle = d.styles.DimmedDesc
	} else if isSelected {
		titleStyle = d.styles.SelectedTitle
		descStyle = d.styles.SelectedDesc
	} else {
		titleStyle = d.styles.NormalTitle
		descStyle = d.styles.NormalDesc
	}

	title := statusItem.Title()
	desc := statusItem.Description()

	if isSelected {
		title = "❯ " + title
	} else {
		title = "  " + title
	}

	fmt.Fprint(w, titleStyle.Render(title))
	fmt.Fprint(w, "\n")
	fmt.Fprint(w, descStyle.Render("  "+desc))
}

// CreateStatusList creates a new status list from tool items
func CreateStatusList(items []types.ToolItem, width, height int) list.Model {
	listItems := make([]list.Item, len(items))
	for i, item := range items {
		listItems[i] = StatusItem{toolItem: item}
	}

	delegate := NewStatusListDelegate()
	l := list.New(listItems, delegate, width, height)
	l.SetShowStatusBar(false)
	l.SetFilteringEnabled(true)
	l.SetShowHelp(false)
	
	return l
}