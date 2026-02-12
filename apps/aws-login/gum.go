package main

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

// gumAvailable checks if the gum CLI is installed
func gumAvailable() bool {
	_, err := exec.LookPath("gum")
	return err == nil
}

// isInteractive checks if stdin is a terminal (not piped)
func isInteractive() bool {
	fi, err := os.Stdin.Stat()
	if err != nil {
		return false
	}
	return fi.Mode()&os.ModeCharDevice != 0
}

// gumChoose presents an interactive chooser and returns the selected item.
// Falls back to returning an error if gum is not available or not interactive.
func gumChoose(header string, items []string) (string, error) {
	if !gumAvailable() || !isInteractive() {
		return "", fmt.Errorf("interactive selection not available")
	}

	args := []string{"choose", "--header", header}
	args = append(args, items...)

	cmd := exec.Command("gum", args...)
	cmd.Stdin = os.Stdin
	cmd.Stderr = os.Stderr

	var out bytes.Buffer
	cmd.Stdout = &out

	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("profile selection cancelled")
	}

	return strings.TrimSpace(out.String()), nil
}

// gumSpin runs a command with a spinner and title. Returns the command's
// combined stdout. Falls back to running the command directly without a
// spinner when gum is not available.
func gumSpin(title string, name string, args ...string) ([]byte, error) {
	if gumAvailable() && isInteractive() {
		gumArgs := []string{
			"spin",
			"--spinner", "dot",
			"--title", title,
			"--show-output",
			"--", name,
		}
		gumArgs = append(gumArgs, args...)

		cmd := exec.Command("gum", gumArgs...)
		cmd.Stdin = os.Stdin
		cmd.Stderr = os.Stderr

		return cmd.Output()
	}

	// Fallback: run directly
	cmd := exec.Command(name, args...)
	return cmd.Output()
}

// gumSpinWithEnv is like gumSpin but allows setting custom environment variables.
func gumSpinWithEnv(title string, env []string, name string, args ...string) ([]byte, error) {
	if gumAvailable() && isInteractive() {
		gumArgs := []string{
			"spin",
			"--spinner", "dot",
			"--title", title,
			"--show-output",
			"--", name,
		}
		gumArgs = append(gumArgs, args...)

		cmd := exec.Command("gum", gumArgs...)
		cmd.Env = env
		cmd.Stdin = os.Stdin
		cmd.Stderr = os.Stderr

		return cmd.Output()
	}

	// Fallback: run directly
	cmd := exec.Command(name, args...)
	cmd.Env = env
	return cmd.Output()
}

// Styled output helpers — these write to stderr like the existing Log functions.
// When gum is unavailable, they fall back to plain text output.

// gumStyleSuccess prints a success message with green styling
func gumStyleSuccess(msg string) {
	if gumAvailable() && isInteractive() {
		cmd := exec.Command("gum", "style",
			"--foreground", "10",
			"--bold",
			msg)
		cmd.Stderr = os.Stderr
		var out bytes.Buffer
		cmd.Stdout = &out
		if err := cmd.Run(); err == nil {
			fmt.Fprint(os.Stderr, out.String())
			return
		}
	}
	fmt.Fprintln(os.Stderr, msg)
}

// gumStyleError prints an error message with red styling
func gumStyleError(msg string) {
	if gumAvailable() && isInteractive() {
		cmd := exec.Command("gum", "style",
			"--foreground", "9",
			"--bold",
			msg)
		cmd.Stderr = os.Stderr
		var out bytes.Buffer
		cmd.Stdout = &out
		if err := cmd.Run(); err == nil {
			fmt.Fprint(os.Stderr, out.String())
			return
		}
	}
	fmt.Fprintln(os.Stderr, msg)
}

// gumStyleInfo prints an info message with blue styling
func gumStyleInfo(msg string) {
	if gumAvailable() && isInteractive() {
		cmd := exec.Command("gum", "style",
			"--foreground", "12",
			msg)
		cmd.Stderr = os.Stderr
		var out bytes.Buffer
		cmd.Stdout = &out
		if err := cmd.Run(); err == nil {
			fmt.Fprint(os.Stderr, out.String())
			return
		}
	}
	fmt.Fprintln(os.Stderr, msg)
}
