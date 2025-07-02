package components

import (
	"testing"

	tea "github.com/charmbracelet/bubbletea"
)

func TestNewProgressComponent(t *testing.T) {
	width := 80
	comp := NewProgressComponent(width)
	
	if comp.width != width {
		t.Errorf("Expected width to be %d, got %d", width, comp.width)
	}
	
	if comp.showSpinner {
		t.Error("Expected showSpinner to be false by default")
	}
	
	if comp.message != "" {
		t.Error("Expected message to be empty by default")
	}
}

func TestProgressComponent_SetMessage(t *testing.T) {
	comp := NewProgressComponent(80)
	message := "Testing progress..."
	
	comp.SetMessage(message)
	
	if comp.message != message {
		t.Errorf("Expected message to be '%s', got '%s'", message, comp.message)
	}
}

func TestProgressComponent_SetSpinner(t *testing.T) {
	comp := NewProgressComponent(80)
	
	if comp.showSpinner {
		t.Error("Expected showSpinner to be false initially")
	}
	
	comp.SetSpinner(true)
	
	if !comp.showSpinner {
		t.Error("Expected showSpinner to be true after SetSpinner(true)")
	}
	
	comp.SetSpinner(false)
	
	if comp.showSpinner {
		t.Error("Expected showSpinner to be false after SetSpinner(false)")
	}
}

func TestProgressComponent_Update(t *testing.T) {
	comp := NewProgressComponent(80)
	
	// Test with spinner tick message
	comp.SetSpinner(true)
	
	// Create a mock window size message
	mockMsg := tea.WindowSizeMsg{Width: 100, Height: 50}
	
	updatedComp, cmd := comp.Update(mockMsg)
	
	// Should return updated component
	if updatedComp.width != comp.width {
		t.Error("Expected Update to return component with same width")
	}
	
	// Command might be nil or non-nil depending on message type
	_ = cmd // Acknowledge we're not checking cmd in this simple test
}

func TestProgressComponent_View(t *testing.T) {
	comp := NewProgressComponent(80)
	comp.SetMessage("Testing...")
	
	view := comp.View()
	
	if view == "" {
		t.Error("Expected View to return non-empty string")
	}
	
	// Test with spinner
	comp.SetSpinner(true)
	viewWithSpinner := comp.View()
	
	if viewWithSpinner == "" {
		t.Error("Expected View with spinner to return non-empty string")
	}
}

func TestProgressMsg(t *testing.T) {
	comp := NewProgressComponent(80)
	
	// Test ProgressMsg update
	msg := ProgressMsg{
		Percent: 0.5,
		Message: "50% complete",
	}
	
	updatedComp, cmd := comp.Update(msg)
	
	if updatedComp.message != msg.Message {
		t.Errorf("Expected message to be '%s', got '%s'", msg.Message, updatedComp.message)
	}
	
	if updatedComp.showSpinner {
		t.Error("Expected showSpinner to be false with valid percent")
	}
	
	if cmd == nil {
		t.Error("Expected ProgressMsg to return a command")
	}
}

func TestCompleteMsg(t *testing.T) {
	comp := NewProgressComponent(80)
	comp.SetSpinner(true) // Start with spinner
	
	// Test successful completion
	msg := CompleteMsg{
		Success: true,
		Message: "Task completed successfully",
	}
	
	updatedComp, cmd := comp.Update(msg)
	
	if updatedComp.message != msg.Message {
		t.Errorf("Expected message to be '%s', got '%s'", msg.Message, updatedComp.message)
	}
	
	if updatedComp.showSpinner {
		t.Error("Expected showSpinner to be false after completion")
	}
	
	if cmd == nil {
		t.Error("Expected successful CompleteMsg to return a command")
	}
	
	// Test failed completion
	failMsg := CompleteMsg{
		Success: false,
		Message: "Task failed",
	}
	
	updatedComp2, cmd2 := comp.Update(failMsg)
	
	if updatedComp2.message != failMsg.Message {
		t.Errorf("Expected message to be '%s', got '%s'", failMsg.Message, updatedComp2.message)
	}
	
	if cmd2 != nil {
		t.Error("Expected failed CompleteMsg to return nil command")
	}
}

// Test OperationProgress
func TestNewOperationProgress(t *testing.T) {
	steps := []string{"Step 1", "Step 2", "Step 3"}
	op := NewOperationProgress(steps)
	
	if op.total != len(steps) {
		t.Errorf("Expected total to be %d, got %d", len(steps), op.total)
	}
	
	if op.current != 0 {
		t.Error("Expected current to be 0 initially")
	}
	
	if len(op.steps) != len(steps) {
		t.Errorf("Expected %d steps, got %d", len(steps), len(op.steps))
	}
	
	if len(op.errors) != 0 {
		t.Error("Expected no errors initially")
	}
}

func TestOperationProgress_NextStep(t *testing.T) {
	steps := []string{"Step 1", "Step 2"}
	op := NewOperationProgress(steps)
	
	if op.current != 0 {
		t.Error("Expected current to be 0 initially")
	}
	
	op.NextStep()
	if op.current != 1 {
		t.Errorf("Expected current to be 1 after NextStep, got %d", op.current)
	}
	
	op.NextStep()
	if op.current != 2 {
		t.Errorf("Expected current to be 2 after second NextStep, got %d", op.current)
	}
	
	// Should not go beyond total
	op.NextStep()
	if op.current != 2 {
		t.Errorf("Expected current to remain 2 after exceeding total, got %d", op.current)
	}
}

func TestOperationProgress_Progress(t *testing.T) {
	steps := []string{"Step 1", "Step 2", "Step 3", "Step 4"}
	op := NewOperationProgress(steps)
	
	// 0% progress initially
	if op.Progress() != 0.0 {
		t.Errorf("Expected initial progress to be 0.0, got %f", op.Progress())
	}
	
	// 25% after first step
	op.NextStep()
	expected := 0.25
	if op.Progress() != expected {
		t.Errorf("Expected progress to be %f, got %f", expected, op.Progress())
	}
	
	// 50% after second step
	op.NextStep()
	expected = 0.5
	if op.Progress() != expected {
		t.Errorf("Expected progress to be %f, got %f", expected, op.Progress())
	}
}

func TestOperationProgress_CurrentStep(t *testing.T) {
	steps := []string{"Step 1", "Step 2", "Step 3"}
	op := NewOperationProgress(steps)
	
	// No current step initially
	if op.CurrentStep() != "" {
		t.Errorf("Expected current step to be empty initially, got '%s'", op.CurrentStep())
	}
	
	op.NextStep()
	if op.CurrentStep() != "Step 1" {
		t.Errorf("Expected current step to be 'Step 1', got '%s'", op.CurrentStep())
	}
	
	op.NextStep()
	if op.CurrentStep() != "Step 2" {
		t.Errorf("Expected current step to be 'Step 2', got '%s'", op.CurrentStep())
	}
}

func TestOperationProgress_Errors(t *testing.T) {
	steps := []string{"Step 1", "Step 2"}
	op := NewOperationProgress(steps)
	
	if op.HasErrors() {
		t.Error("Expected no errors initially")
	}
	
	op.AddError("Test error")
	
	if !op.HasErrors() {
		t.Error("Expected to have errors after adding one")
	}
	
	if len(op.errors) != 1 {
		t.Errorf("Expected 1 error, got %d", len(op.errors))
	}
	
	op.AddError("Another error")
	if len(op.errors) != 2 {
		t.Errorf("Expected 2 errors, got %d", len(op.errors))
	}
}

func TestOperationProgress_IsComplete(t *testing.T) {
	steps := []string{"Step 1", "Step 2"}
	op := NewOperationProgress(steps)
	
	if op.IsComplete() {
		t.Error("Expected not to be complete initially")
	}
	
	op.NextStep()
	if op.IsComplete() {
		t.Error("Expected not to be complete after one step")
	}
	
	op.NextStep()
	if !op.IsComplete() {
		t.Error("Expected to be complete after all steps")
	}
}

func TestOperationProgress_View(t *testing.T) {
	steps := []string{"Step 1", "Step 2"}
	op := NewOperationProgress(steps)
	
	// Test view in progress
	view := op.View()
	if view == "" {
		t.Error("Expected view to return non-empty string")
	}
	
	// Test view when complete without errors
	op.NextStep()
	op.NextStep()
	completeView := op.View()
	if completeView == "" {
		t.Error("Expected complete view to return non-empty string")
	}
	
	// Test view when complete with errors
	op.AddError("Test error")
	errorView := op.View()
	if errorView == "" {
		t.Error("Expected error view to return non-empty string")
	}
}