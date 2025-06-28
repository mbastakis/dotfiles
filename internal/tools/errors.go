package tools

import "errors"

var (
	// Tool registration errors
	ErrInvalidToolName = errors.New("tool name cannot be empty")
	ErrToolNotFound    = errors.New("tool not found")
	ErrToolDisabled    = errors.New("tool is disabled")
	
	// Configuration errors
	ErrInvalidConfig   = errors.New("invalid tool configuration")
	ErrMissingConfig   = errors.New("missing required configuration")
	
	// Operation errors
	ErrOperationFailed = errors.New("tool operation failed")
	ErrValidationFailed = errors.New("tool validation failed")
	ErrDependencyMissing = errors.New("required dependency missing")
	
	// Stow-specific errors
	ErrStowNotFound     = errors.New("stow command not found")
	ErrPackageNotFound  = errors.New("stow package not found")
	ErrTargetNotFound   = errors.New("target directory not found")
	ErrConflictDetected = errors.New("file conflict detected")
)