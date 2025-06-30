package common

import tea "github.com/charmbracelet/bubbletea"

// NavigateMsg represents navigation to a new screen
type NavigateMsg struct {
	Screen tea.Model
}

// BackMsg represents going back to the previous screen  
type BackMsg struct{}