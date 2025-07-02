package common

import (
	"context"
	"log/slog"
	"os"
	"regexp"
	"strings"
	"sync"
)

var (
	defaultLogger *slog.Logger
	loggerOnce    sync.Once
)

// InitLogger initializes the global logger with the specified level and format
func InitLogger(level slog.Level, verbose bool) {
	loggerOnce.Do(func() {
		var handler slog.Handler
		
		opts := &slog.HandlerOptions{
			Level: level,
		}
		
		if verbose {
			// Use text handler for verbose mode (more readable for debugging)
			handler = slog.NewTextHandler(os.Stdout, opts)
		} else {
			// Use text handler for non-verbose mode as well for cleaner CLI output
			// Remove timestamp and level for clean output
			opts.ReplaceAttr = func(groups []string, a slog.Attr) slog.Attr {
				// Remove time and level for cleaner output
				if a.Key == slog.TimeKey || a.Key == slog.LevelKey {
					return slog.Attr{}
				}
				return a
			}
			handler = slog.NewTextHandler(os.Stdout, opts)
		}
		
		defaultLogger = slog.New(handler)
		slog.SetDefault(defaultLogger)
	})
}

// GetLogger returns the global logger, initializing it if necessary
func GetLogger() *slog.Logger {
	if defaultLogger == nil {
		InitLogger(slog.LevelInfo, false)
	}
	return defaultLogger
}

// LoggerForTool creates a logger with tool-specific context
func LoggerForTool(toolName string) *slog.Logger {
	return GetLogger().With("tool", toolName)
}

// LogSuccess logs a success message (always visible)
func LogSuccess(logger *slog.Logger, msg string, args ...any) {
	logger.Info("✅ "+msg, args...)
}

// LogError logs an error message (always visible)
func LogError(logger *slog.Logger, msg string, args ...any) {
	logger.Error("❌ "+msg, args...)
}

// LogWarning logs a warning message
func LogWarning(logger *slog.Logger, msg string, args ...any) {
	logger.Warn("⚠️ "+msg, args...)
}

// LogInfo logs an info message (verbose mode only)
func LogInfo(logger *slog.Logger, msg string, args ...any) {
	logger.Info(msg, args...)
}

// LogDebug logs a debug message (verbose mode only)
func LogDebug(logger *slog.Logger, msg string, args ...any) {
	logger.Debug("🔍 "+msg, args...)
}

// ScriptOutputFilter filters and processes script output based on log level
type ScriptOutputFilter struct {
	logger  *slog.Logger
	verbose bool
	buffer  strings.Builder
}

// NewScriptOutputFilter creates a new script output filter
func NewScriptOutputFilter(logger *slog.Logger, verbose bool) *ScriptOutputFilter {
	return &ScriptOutputFilter{
		logger:  logger,
		verbose: verbose,
	}
}

// Write implements io.Writer interface
func (f *ScriptOutputFilter) Write(p []byte) (n int, err error) {
	f.buffer.Write(p)
	
	// Process complete lines
	for {
		content := f.buffer.String()
		lineEnd := strings.Index(content, "\n")
		if lineEnd == -1 {
			break
		}
		
		line := strings.TrimSpace(content[:lineEnd])
		f.buffer.Reset()
		f.buffer.WriteString(content[lineEnd+1:])
		
		if line != "" {
			f.processLine(line)
		}
	}
	
	return len(p), nil
}

// Flush processes any remaining content in the buffer
func (f *ScriptOutputFilter) Flush() {
	if f.buffer.Len() > 0 {
		line := strings.TrimSpace(f.buffer.String())
		if line != "" {
			f.processLine(line)
		}
		f.buffer.Reset()
	}
}

// processLine processes a single line of script output
func (f *ScriptOutputFilter) processLine(line string) {
	// Clean the line first
	cleanLine := f.cleanLine(line)
	if cleanLine == "" {
		return
	}
	
	// Determine log level based on patterns
	level := f.detectLogLevel(cleanLine)
	
	// Filter based on verbosity and log level
	if f.shouldShowLine(level, cleanLine) {
		f.logLine(level, cleanLine)
	}
}

// detectLogLevel determines the log level based on line content
func (f *ScriptOutputFilter) detectLogLevel(line string) slog.Level {
	// Error patterns
	errorPatterns := []*regexp.Regexp{
		regexp.MustCompile(`(?i)\[(ERROR|FAIL|FATAL)\]`),
		regexp.MustCompile(`(?i)^\s*(❌|✗|ERROR|FAIL|FATAL)`),
		regexp.MustCompile(`(?i)failed`),
		regexp.MustCompile(`(?i)error:`),
	}
	
	// Warning patterns
	warnPatterns := []*regexp.Regexp{
		regexp.MustCompile(`(?i)\[(WARN|WARNING)\]`),
		regexp.MustCompile(`(?i)^\s*(⚠️|WARNING|WARN)`),
		regexp.MustCompile(`(?i)may already be installed`),
	}
	
	// Success patterns (treated as info but always shown)
	successPatterns := []*regexp.Regexp{
		regexp.MustCompile(`(?i)\[(SUCCESS|DONE)\]`),
		regexp.MustCompile(`(?i)^\s*(✅|✓|SUCCESS|DONE|COMPLETE)`),
		regexp.MustCompile(`(?i)successfully`),
		regexp.MustCompile(`(?i)installation complete`),
	}
	
	// Debug patterns
	debugPatterns := []*regexp.Regexp{
		regexp.MustCompile(`(?i)\[(DEBUG|VERBOSE)\]`),
		regexp.MustCompile(`(?i)^\s*Files included`),
		regexp.MustCompile(`(?i)^\s*VSIX file created`),
	}
	
	// Check patterns in order of priority
	for _, pattern := range errorPatterns {
		if pattern.MatchString(line) {
			return slog.LevelError
		}
	}
	
	for _, pattern := range warnPatterns {
		if pattern.MatchString(line) {
			return slog.LevelWarn
		}
	}
	
	for _, pattern := range successPatterns {
		if pattern.MatchString(line) {
			return slog.LevelInfo
		}
	}
	
	for _, pattern := range debugPatterns {
		if pattern.MatchString(line) {
			return slog.LevelDebug
		}
	}
	
	// Default to info level
	return slog.LevelInfo
}

// shouldShowLine determines if a line should be shown based on verbosity and level
func (f *ScriptOutputFilter) shouldShowLine(level slog.Level, line string) bool {
	if f.verbose {
		return true // Show everything in verbose mode
	}
	
	// In non-verbose mode, show errors, warnings, and important success messages
	if level == slog.LevelError || level == slog.LevelWarn {
		return true
	}
	
	// Check for important success patterns
	importantPatterns := []*regexp.Regexp{
		regexp.MustCompile(`(?i)successfully installed:`),
		regexp.MustCompile(`(?i)installation complete`),
		regexp.MustCompile(`(?i)setup complete`),
		regexp.MustCompile(`(?i)^\s*===.*===$`),
		regexp.MustCompile(`(?i)^\s*---.*---$`),
	}
	
	for _, pattern := range importantPatterns {
		if pattern.MatchString(line) {
			return true
		}
	}
	
	return false
}

// logLine logs the line at the appropriate level
func (f *ScriptOutputFilter) logLine(level slog.Level, line string) {
	ctx := context.Background()
	
	switch level {
	case slog.LevelError:
		f.logger.ErrorContext(ctx, line)
	case slog.LevelWarn:
		f.logger.WarnContext(ctx, line)
	case slog.LevelDebug:
		f.logger.DebugContext(ctx, line)
	default:
		f.logger.InfoContext(ctx, line)
	}
}

// cleanLine cleans up a log line for consistent formatting
func (f *ScriptOutputFilter) cleanLine(line string) string {
	// Remove ANSI color codes
	ansiRegex := regexp.MustCompile(`\x1b\[[0-9;]*[a-zA-Z]`)
	cleaned := ansiRegex.ReplaceAllString(line, "")
	
	// Remove redundant log prefixes since slog will handle formatting
	prefixPatterns := []*regexp.Regexp{
		regexp.MustCompile(`^\[INFO\]\s*`),
		regexp.MustCompile(`^\[ERROR\]\s*`),
		regexp.MustCompile(`^\[WARNING\]\s*`),
		regexp.MustCompile(`^\[SUCCESS\]\s*`),
		regexp.MustCompile(`^\[DONE\]\s*`),
		regexp.MustCompile(`^\[DEBUG\]\s*`),
	}
	
	for _, pattern := range prefixPatterns {
		cleaned = pattern.ReplaceAllString(cleaned, "")
	}
	
	return strings.TrimSpace(cleaned)
}