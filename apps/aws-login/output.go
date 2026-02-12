package main

import (
	"fmt"
	"os/exec"
)

var verbose bool

// SetVerbose sets the verbose mode
func SetVerbose(v bool) {
	verbose = v
}

// LogInfo prints an info message to stderr, styled with gum when available
func LogInfo(format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	gumStyleInfo(msg)
}

// LogVerbose prints a message to stderr only if verbose mode is enabled
func LogVerbose(format string, args ...interface{}) {
	if verbose {
		msg := fmt.Sprintf(format, args...)
		gumStyleInfo(msg)
	}
}

// LogError prints an error message to stderr, styled with gum when available
func LogError(format string, args ...interface{}) {
	msg := fmt.Sprintf("Error: "+format, args...)
	gumStyleError(msg)
}

// LogSuccess prints a success message to stderr, styled with gum when available
func LogSuccess(format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	gumStyleSuccess(msg)
}

// PrintExport prints an export command to stdout
func PrintExport(key, value string) {
	fmt.Printf("export %s='%s'\n", key, value)
}

// RunCommand runs a command silently (for starship-timer, etc.)
func RunCommand(name string, args ...string) error {
	cmd := exec.Command(name, args...)
	return cmd.Run()
}
