package main

import (
	"fmt"
	"os"
	"os/exec"
)

var verbose bool

// SetVerbose sets the verbose mode
func SetVerbose(v bool) {
	verbose = v
}

// LogInfo prints an info message to stderr
func LogInfo(format string, args ...interface{}) {
	fmt.Fprintf(os.Stderr, format+"\n", args...)
}

// LogVerbose prints a message to stderr only if verbose mode is enabled
func LogVerbose(format string, args ...interface{}) {
	if verbose {
		fmt.Fprintf(os.Stderr, format+"\n", args...)
	}
}

// LogError prints an error message to stderr
func LogError(format string, args ...interface{}) {
	fmt.Fprintf(os.Stderr, "Error: "+format+"\n", args...)
}

// RunCommand runs a command silently (for starship-timer, etc.)
func RunCommand(name string, args ...string) error {
	cmd := exec.Command(name, args...)
	return cmd.Run()
}
