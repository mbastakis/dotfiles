package tools

import (
	"context"
	"sync"

	"github.com/yourusername/dotfiles/internal/types"
)

// Tool interface that all tools must implement
type Tool interface {
	// Basic tool information
	Name() string
	IsEnabled() bool
	Priority() int

	// Tool validation and health checks
	Validate() error
	Status(ctx context.Context) (*types.ToolStatus, error)

	// Core operations
	Install(ctx context.Context, items []string) (*types.OperationResult, error)
	Update(ctx context.Context, items []string) (*types.OperationResult, error)
	Remove(ctx context.Context, items []string) (*types.OperationResult, error)
	List(ctx context.Context) ([]types.ToolItem, error)
	Sync(ctx context.Context) (*types.OperationResult, error)

	// Configuration management
	Configure(config interface{}) error
}

// CategoryTool interface for tools that support category-level operations
type CategoryTool interface {
	Tool
	
	// Category-level operations
	ListCategoryItems(ctx context.Context, category string) ([]types.ToolItem, error)
	InstallCategoryItem(ctx context.Context, category string, item string) (*types.OperationResult, error)
	SupportsCategories() bool
}

// ToolRegistry manages all available tools
type ToolRegistry struct {
	mu    sync.RWMutex
	tools map[string]Tool
}

// NewToolRegistry creates a new tool registry
func NewToolRegistry() *ToolRegistry {
	return &ToolRegistry{
		tools: make(map[string]Tool),
	}
}

// Register adds a tool to the registry
func (r *ToolRegistry) Register(tool Tool) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	if tool.Name() == "" {
		return ErrInvalidToolName
	}
	
	r.tools[tool.Name()] = tool
	return nil
}

// Get retrieves a tool by name
func (r *ToolRegistry) Get(name string) (Tool, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	
	tool, exists := r.tools[name]
	return tool, exists
}

// List returns all registered tools
func (r *ToolRegistry) List() []Tool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	
	tools := make([]Tool, 0, len(r.tools))
	for _, tool := range r.tools {
		tools = append(tools, tool)
	}
	return tools
}

// ListEnabled returns only enabled tools
func (r *ToolRegistry) ListEnabled() []Tool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	
	var enabled []Tool
	for _, tool := range r.tools {
		if tool.IsEnabled() {
			enabled = append(enabled, tool)
		}
	}
	return enabled
}

// Remove removes a tool from the registry
func (r *ToolRegistry) Remove(name string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	
	delete(r.tools, name)
}

// GetByPriority returns tools sorted by priority (lower numbers first)
func (r *ToolRegistry) GetByPriority() []Tool {
	tools := r.ListEnabled()
	
	// Sort by priority
	for i := 0; i < len(tools); i++ {
		for j := i + 1; j < len(tools); j++ {
			if tools[i].Priority() > tools[j].Priority() {
				tools[i], tools[j] = tools[j], tools[i]
			}
		}
	}
	
	return tools
}