package components

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/progress"
	"github.com/charmbracelet/bubbles/spinner"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// ProgressComponent represents a progress indicator with optional spinner
type ProgressComponent struct {
	progress  progress.Model
	spinner   spinner.Model
	showSpinner bool
	message   string
	width     int
	styles    ProgressStyles
}

type ProgressStyles struct {
	Message    lipgloss.Style
	Complete   lipgloss.Style
	Error      lipgloss.Style
}

// NewProgressComponent creates a new progress component
func NewProgressComponent(width int) ProgressComponent {
	p := progress.New(progress.WithDefaultGradient())
	p.Width = width - 4 // Account for padding

	s := spinner.New()
	s.Spinner = spinner.Dot
	s.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("205"))

	return ProgressComponent{
		progress: p,
		spinner:  s,
		width:    width,
		styles: ProgressStyles{
			Message: lipgloss.NewStyle().
				Foreground(lipgloss.Color("246")).
				Padding(0, 1),
			Complete: lipgloss.NewStyle().
				Foreground(lipgloss.Color("42")).
				Bold(true).
				Padding(0, 1),
			Error: lipgloss.NewStyle().
				Foreground(lipgloss.Color("196")).
				Bold(true).
				Padding(0, 1),
		},
	}
}

// ProgressMsg represents a progress update message
type ProgressMsg struct {
	Percent float64
	Message string
}

// CompleteMsg represents completion
type CompleteMsg struct {
	Success bool
	Message string
}

// Init initializes the progress component
func (p ProgressComponent) Init() tea.Cmd {
	if p.showSpinner {
		return p.spinner.Tick
	}
	return nil
}

// Update handles progress component updates
func (p ProgressComponent) Update(msg tea.Msg) (ProgressComponent, tea.Cmd) {
	switch msg := msg.(type) {
	case ProgressMsg:
		p.message = msg.Message
		if msg.Percent >= 0 {
			p.showSpinner = false
			return p, p.progress.SetPercent(msg.Percent)
		} else {
			p.showSpinner = true
			var cmd tea.Cmd
			p.spinner, cmd = p.spinner.Update(msg)
			return p, cmd
		}

	case CompleteMsg:
		p.showSpinner = false
		p.message = msg.Message
		if msg.Success {
			return p, p.progress.SetPercent(1.0)
		}
		return p, nil

	case progress.FrameMsg:
		progressModel, cmd := p.progress.Update(msg)
		p.progress = progressModel.(progress.Model)
		return p, cmd

	case spinner.TickMsg:
		if p.showSpinner {
			var cmd tea.Cmd
			p.spinner, cmd = p.spinner.Update(msg)
			return p, cmd
		}
	}

	return p, nil
}

// View renders the progress component
func (p ProgressComponent) View() string {
	var parts []string

	if p.message != "" {
		parts = append(parts, p.styles.Message.Render(p.message))
	}

	if p.showSpinner {
		parts = append(parts, p.spinner.View()+" Working...")
	} else {
		parts = append(parts, p.progress.View())
	}

	return strings.Join(parts, "\n")
}

// SetMessage updates the progress message
func (p *ProgressComponent) SetMessage(message string) {
	p.message = message
}

// SetSpinner enables or disables the spinner
func (p *ProgressComponent) SetSpinner(show bool) {
	p.showSpinner = show
}

// OperationProgress tracks progress of a multi-step operation
type OperationProgress struct {
	current int
	total   int
	steps   []string
	errors  []string
	styles  ProgressStyles
}

// NewOperationProgress creates a new operation progress tracker
func NewOperationProgress(steps []string) OperationProgress {
	return OperationProgress{
		current: 0,
		total:   len(steps),
		steps:   steps,
		errors:  make([]string, 0),
		styles: ProgressStyles{
			Message: lipgloss.NewStyle().
				Foreground(lipgloss.Color("246")),
			Complete: lipgloss.NewStyle().
				Foreground(lipgloss.Color("42")).
				Bold(true),
			Error: lipgloss.NewStyle().
				Foreground(lipgloss.Color("196")).
				Bold(true),
		},
	}
}

// NextStep advances to the next step
func (op *OperationProgress) NextStep() {
	if op.current < op.total {
		op.current++
	}
}

// AddError adds an error to the current step
func (op *OperationProgress) AddError(err string) {
	op.errors = append(op.errors, err)
}

// CurrentStep returns the current step name
func (op *OperationProgress) CurrentStep() string {
	if op.current > 0 && op.current <= len(op.steps) {
		return op.steps[op.current-1]
	}
	return ""
}

// Progress returns the current progress as a percentage
func (op *OperationProgress) Progress() float64 {
	if op.total == 0 {
		return 1.0
	}
	return float64(op.current) / float64(op.total)
}

// IsComplete returns true if all steps are completed
func (op *OperationProgress) IsComplete() bool {
	return op.current >= op.total
}

// HasErrors returns true if there are any errors
func (op *OperationProgress) HasErrors() bool {
	return len(op.errors) > 0
}

// View renders the operation progress
func (op *OperationProgress) View() string {
	var parts []string

	// Progress bar
	progressBar := progress.New(progress.WithDefaultGradient())
	progressBar.Width = 40
	parts = append(parts, progressBar.ViewAs(op.Progress()))

	// Current step
	if !op.IsComplete() && op.current < len(op.steps) {
		currentStep := fmt.Sprintf("Step %d/%d: %s", op.current+1, op.total, op.steps[op.current])
		parts = append(parts, op.styles.Message.Render(currentStep))
	} else if op.IsComplete() {
		if op.HasErrors() {
			parts = append(parts, op.styles.Error.Render("⚠️ Completed with errors"))
		} else {
			parts = append(parts, op.styles.Complete.Render("✅ Completed successfully"))
		}
	}

	// Errors
	if op.HasErrors() {
		parts = append(parts, "")
		parts = append(parts, op.styles.Error.Render("Errors:"))
		for _, err := range op.errors {
			parts = append(parts, op.styles.Error.Render("  • "+err))
		}
	}

	return strings.Join(parts, "\n")
}