package main

import (
	"os"
	"os/exec"
	"strings"
)

// GetTOTPFromBitwarden retrieves a TOTP code from Bitwarden
func GetTOTPFromBitwarden(itemName string) (string, error) {
	// Get or unlock BW session
	session, err := getBWSession()
	if err != nil {
		return "", err
	}

	// Get TOTP with spinner
	output, err := gumSpin("Fetching MFA code from Bitwarden...",
		"bw", "get", "totp", itemName, "--session", session)
	if err != nil {
		return "", err
	}

	return strings.TrimSpace(string(output)), nil
}

func getBWSession() (string, error) {
	// Check if BW_SESSION is set and valid
	session := os.Getenv("BW_SESSION")
	if session != "" {
		cmd := exec.Command("bw", "unlock", "--check", "--session", session)
		if err := cmd.Run(); err == nil {
			return session, nil
		}
	}

	// Check if logged in
	cmd := exec.Command("bw", "login", "--check")
	if err := cmd.Run(); err != nil {
		LogError("Not logged into Bitwarden. Please run 'bw login' first.")
		return "", err
	}

	// Unlock vault
	LogVerbose("Bitwarden vault is locked. Please enter your master password:")
	cmd = exec.Command("bw", "unlock", "--raw")
	cmd.Stdin = os.Stdin
	cmd.Stderr = os.Stderr

	output, err := cmd.Output()
	if err != nil {
		return "", err
	}

	session = strings.TrimSpace(string(output))

	// Export for future use (captured by shell wrapper)
	PrintExport("BW_SESSION", session)

	return session, nil
}
