package types

import "time"

// ToolStatus represents the current status of a tool
type ToolStatus struct {
	Name      string    `json:"name"`
	Enabled   bool      `json:"enabled"`
	Healthy   bool      `json:"healthy"`
	LastCheck time.Time `json:"last_check"`
	Error     error     `json:"error,omitempty"`
	Items     []ToolItem `json:"items,omitempty"`
}

// ToolItem represents an individual item managed by a tool (package, formula, etc.)
type ToolItem struct {
	Name        string            `json:"name"`
	Enabled     bool             `json:"enabled"`
	Installed   bool             `json:"installed"`
	Version     string           `json:"version,omitempty"`
	Target      string           `json:"target,omitempty"`
	Priority    int              `json:"priority,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// OperationResult represents the result of a tool operation
type OperationResult struct {
	Success   bool     `json:"success"`
	Message   string   `json:"message"`
	Error     error    `json:"error,omitempty"`
	Output    string   `json:"output,omitempty"`
	Modified  []string `json:"modified,omitempty"`
}