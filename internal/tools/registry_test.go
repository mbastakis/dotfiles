package tools

import (
	"context"
	"testing"

	"github.com/mbastakis/dotfiles/internal/types"
)

func TestNewToolRegistry(t *testing.T) {
	registry := NewToolRegistry()
	if registry == nil {
		t.Fatal("Expected NewToolRegistry to return non-nil registry")
	}

	// Should start empty
	tools := registry.List()
	if len(tools) != 0 {
		t.Errorf("Expected new registry to be empty, got %d tools", len(tools))
	}
}

func TestToolRegistry_Register(t *testing.T) {
	registry := NewToolRegistry()

	// Create a mock tool
	mockTool := &MockTool{
		name:    "mock",
		enabled: true,
	}

	err := registry.Register(mockTool)
	if err != nil {
		t.Fatalf("Expected Register to succeed, got: %v", err)
	}

	tools := registry.List()
	if len(tools) != 1 {
		t.Errorf("Expected 1 tool after registration, got %d", len(tools))
	}

	// Check that mock tool is present
	found := false
	for _, tool := range tools {
		if tool.Name() == "mock" {
			found = true
			break
		}
	}
	if !found {
		t.Error("Expected mock tool to be registered")
	}
}

func TestToolRegistry_Register_EmptyName(t *testing.T) {
	registry := NewToolRegistry()

	// Create a mock tool with empty name
	mockTool := &MockTool{
		name:    "",
		enabled: true,
	}

	err := registry.Register(mockTool)
	if err == nil {
		t.Fatal("Expected Register to fail with empty tool name")
	}

	if err != ErrInvalidToolName {
		t.Errorf("Expected ErrInvalidToolName, got: %v", err)
	}
}

func TestToolRegistry_Get(t *testing.T) {
	registry := NewToolRegistry()

	// Create and register a mock tool
	mockTool := &MockTool{
		name:    "mock",
		enabled: true,
	}
	registry.Register(mockTool)

	// Test getting existing tool
	tool, exists := registry.Get("mock")
	if !exists {
		t.Fatal("Expected mock tool to exist")
	}
	if tool.Name() != "mock" {
		t.Errorf("Expected tool name to be 'mock', got %s", tool.Name())
	}

	// Test getting non-existent tool
	_, exists = registry.Get("nonexistent")
	if exists {
		t.Error("Expected non-existent tool to not exist")
	}
}

func TestToolRegistry_ListEnabled(t *testing.T) {
	registry := NewToolRegistry()

	// Register enabled and disabled tools
	enabledTool := &MockTool{name: "enabled", enabled: true}
	disabledTool := &MockTool{name: "disabled", enabled: false}

	registry.Register(enabledTool)
	registry.Register(disabledTool)

	enabledTools := registry.ListEnabled()

	// Should have only enabled tools
	if len(enabledTools) != 1 {
		t.Errorf("Expected 1 enabled tool, got %d", len(enabledTools))
	}

	// All returned tools should be enabled
	for _, tool := range enabledTools {
		if !tool.IsEnabled() {
			t.Errorf("Expected tool %s to be enabled", tool.Name())
		}
	}

	if enabledTools[0].Name() != "enabled" {
		t.Errorf("Expected enabled tool to be 'enabled', got %s", enabledTools[0].Name())
	}
}

func TestToolRegistry_Remove(t *testing.T) {
	registry := NewToolRegistry()

	// Create and register a mock tool
	mockTool := &MockTool{
		name:    "mock",
		enabled: true,
	}
	registry.Register(mockTool)

	// Verify tool exists
	_, exists := registry.Get("mock")
	if !exists {
		t.Fatal("Expected mock tool to exist before removal")
	}

	// Remove the tool
	registry.Remove("mock")

	// Verify tool no longer exists
	_, exists = registry.Get("mock")
	if exists {
		t.Error("Expected mock tool to not exist after removal")
	}

	// List should be empty
	tools := registry.List()
	if len(tools) != 0 {
		t.Errorf("Expected 0 tools after removal, got %d", len(tools))
	}
}

func TestToolRegistry_GetByPriority(t *testing.T) {
	registry := NewToolRegistry()

	// Register tools with different priorities
	tool1 := &MockTool{name: "high", enabled: true, priority: 1}
	tool2 := &MockTool{name: "low", enabled: true, priority: 3}
	tool3 := &MockTool{name: "medium", enabled: true, priority: 2}
	tool4 := &MockTool{name: "disabled", enabled: false, priority: 0}

	registry.Register(tool1)
	registry.Register(tool2)
	registry.Register(tool3)
	registry.Register(tool4)

	priorityTools := registry.GetByPriority()

	// Should only include enabled tools
	if len(priorityTools) != 3 {
		t.Errorf("Expected 3 enabled tools, got %d", len(priorityTools))
	}

	// Should be sorted by priority (lower numbers first)
	expectedOrder := []string{"high", "medium", "low"}
	for i, expectedName := range expectedOrder {
		if priorityTools[i].Name() != expectedName {
			t.Errorf("Expected tool at position %d to be %s, got %s", i, expectedName, priorityTools[i].Name())
		}
	}
}

// MockTool is a mock implementation of the Tool interface for testing
type MockTool struct {
	name      string
	enabled   bool
	priority  int
	lastError error
}

func (m *MockTool) Name() string {
	return m.name
}

func (m *MockTool) IsEnabled() bool {
	return m.enabled
}

func (m *MockTool) Priority() int {
	return m.priority
}

func (m *MockTool) Validate() error {
	return m.lastError
}

func (m *MockTool) Status(ctx context.Context) (*types.ToolStatus, error) {
	if m.lastError != nil {
		return nil, m.lastError
	}
	return &types.ToolStatus{
		Name:    m.name,
		Enabled: m.enabled,
		Healthy: true,
		Items: []types.ToolItem{
			{Name: "mock-item", Enabled: true, Installed: true},
		},
	}, nil
}

func (m *MockTool) Install(ctx context.Context, items []string) (*types.OperationResult, error) {
	if m.lastError != nil {
		return nil, m.lastError
	}
	return &types.OperationResult{
		Tool:      m.name,
		Operation: "install",
		Success:   true,
		Message:   "Mock install completed",
		Modified:  items,
	}, nil
}

func (m *MockTool) Update(ctx context.Context, items []string) (*types.OperationResult, error) {
	if m.lastError != nil {
		return nil, m.lastError
	}
	return &types.OperationResult{
		Tool:      m.name,
		Operation: "update",
		Success:   true,
		Message:   "Mock update completed",
		Modified:  items,
	}, nil
}

func (m *MockTool) Remove(ctx context.Context, items []string) (*types.OperationResult, error) {
	if m.lastError != nil {
		return nil, m.lastError
	}
	return &types.OperationResult{
		Tool:      m.name,
		Operation: "remove",
		Success:   true,
		Message:   "Mock remove completed",
		Modified:  items,
	}, nil
}

func (m *MockTool) List(ctx context.Context) ([]types.ToolItem, error) {
	if m.lastError != nil {
		return nil, m.lastError
	}
	return []types.ToolItem{
		{Name: "mock-item", Enabled: true, Installed: true},
	}, nil
}

func (m *MockTool) Sync(ctx context.Context) (*types.OperationResult, error) {
	if m.lastError != nil {
		return nil, m.lastError
	}
	return &types.OperationResult{
		Tool:      m.name,
		Operation: "sync",
		Success:   true,
		Message:   "Mock sync completed",
	}, nil
}

func (m *MockTool) Configure(config interface{}) error {
	return m.lastError
}

// SetError allows setting an error for testing error conditions
func (m *MockTool) SetError(err error) {
	m.lastError = err
}
