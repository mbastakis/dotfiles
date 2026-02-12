package main

import (
	"fmt"
	"os"
	"sort"
)

// Version can be set at build time
var Version = "dev"

func main() {
	args := os.Args[1:]

	// Parse flags
	var profileName string
	var mfaCode string
	var showList bool
	var showStatus bool
	var clearCreds bool
	var noCache bool
	var verbose bool
	var showHelp bool
	var showVersion bool

	i := 0
	for i < len(args) {
		arg := args[i]
		switch arg {
		case "-h", "--help":
			showHelp = true
		case "-v", "--verbose":
			verbose = true
		case "--version":
			showVersion = true
		case "--list":
			showList = true
		case "--status":
			showStatus = true
		case "--clear":
			clearCreds = true
		case "--no-cache":
			noCache = true
		default:
			if arg[0] == '-' {
				LogError("Unknown option: %s", arg)
				os.Exit(1)
			}
			if profileName == "" {
				profileName = arg
			} else if mfaCode == "" {
				mfaCode = arg
			}
		}
		i++
	}

	if showVersion {
		fmt.Fprintf(os.Stderr, "aws-login version %s\n", Version)
		os.Exit(0)
	}

	if showHelp {
		printUsage()
		os.Exit(0)
	}

	// Load configuration
	cfg, err := LoadConfig()
	if err != nil {
		LogError("Failed to load config: %v", err)
		os.Exit(1)
	}

	if showList {
		listProfiles(cfg)
		os.Exit(0)
	}

	if showStatus {
		showCurrentStatus(cfg)
		os.Exit(0)
	}

	if clearCreds {
		clearCredentials()
		os.Exit(0)
	}

	if profileName == "" {
		// Interactive profile selection with gum
		names := getProfileNames(cfg)
		if len(names) == 0 {
			LogError("No profiles configured")
			os.Exit(1)
		}

		// Build display items with descriptions
		items := make([]string, 0, len(names))
		for _, name := range names {
			items = append(items, name)
		}

		selected, err := gumChoose("Select an AWS profile:", items)
		if err != nil {
			LogError("Profile name is required")
			printUsage()
			os.Exit(1)
		}
		profileName = selected
	}

	// Get profile config
	profile, ok := cfg.Profiles[profileName]
	if !ok {
		LogError("Unknown profile: %s", profileName)
		LogInfo("Available profiles: %v", getProfileNames(cfg))
		os.Exit(1)
	}

	// Set verbose mode
	SetVerbose(verbose)

	// Try cache first (unless --no-cache)
	if !noCache {
		cached, err := LoadCache(cfg, profileName)
		if err == nil && cached != nil {
			LogVerbose("Using cached credentials...")
			outputCredentials(cached, profileName, cfg.Defaults.Region)
			reportSuccess(profileName, cached.Identity, cached.RemainingSeconds())
			updateStarshipTimer(cfg, profileName, cached.ExpirationEpoch)
			os.Exit(0)
		}
	}

	// Get fresh credentials based on profile type
	var result *AuthResult
	switch profile.Type {
	case "mfa":
		result, err = AuthMFA(cfg, profileName, profile, mfaCode)
	case "iam":
		result, err = AuthIAM(cfg, profileName, profile)
	default:
		LogError("Unsupported profile type: %s", profile.Type)
		os.Exit(1)
	}

	if err != nil {
		LogError("Authentication failed: %v", err)
		if profile.Type == "iam" {
			LogInfo("")
			LogInfo("Credentials for %s may be expired or invalid", profileName)
			LogInfo("Please update credentials in ~/.aws/credentials")
		}
		os.Exit(1)
	}

	// Save to cache
	SaveCache(cfg, profileName, result)

	// Output credentials
	outputCredentials(result, profileName, cfg.Defaults.Region)

	// Report success
	reportSuccess(profileName, result.Identity, result.RemainingSeconds())

	// Update starship timer
	updateStarshipTimer(cfg, profileName, result.ExpirationEpoch)
}

func printUsage() {
	LogInfo("Usage: aws-login <profile> [mfa-code] [options]")
	LogInfo("")
	LogInfo("Options:")
	LogInfo("  --list        Show available profiles")
	LogInfo("  --status      Show current session status")
	LogInfo("  --clear       Unset AWS environment variables")
	LogInfo("  --no-cache    Force refresh, ignore cached credentials")
	LogInfo("  -v, --verbose Show detailed output")
	LogInfo("  -h, --help    Show this help message")
	LogInfo("  --version     Show version")
	LogInfo("")
	LogInfo("Examples:")
	LogInfo("  aws-login dev              # Switch to dev profile")
	LogInfo("  aws-login playground       # MFA profile (auto-fetch from Bitwarden)")
	LogInfo("  aws-login playground 123456 # MFA with manual code")
}

func listProfiles(cfg *Config) {
	LogInfo("Available profiles:")
	LogInfo("")
	for name, profile := range cfg.Profiles {
		desc := profile.Description
		if desc == "" {
			desc = fmt.Sprintf("%s profile", profile.Type)
		}
		LogInfo("  %-15s %s (%s)", name, desc, profile.Type)
	}
}

func showCurrentStatus(cfg *Config) {
	// Check for cached sessions
	profiles := getProfileNames(cfg)
	foundAny := false

	for _, name := range profiles {
		cached, err := LoadCache(cfg, name)
		if err == nil && cached != nil {
			if !foundAny {
				LogInfo("Active sessions:")
				LogInfo("")
				foundAny = true
			}
			remaining := cached.RemainingSeconds()
			LogInfo("  %-15s %s (expires in %s)", name, cached.Identity.ARN, formatDuration(remaining))
		}
	}

	if !foundAny {
		LogInfo("No active sessions")
	}
}

func clearCredentials() {
	// Output unset commands
	fmt.Println("unset AWS_ACCESS_KEY_ID")
	fmt.Println("unset AWS_SECRET_ACCESS_KEY")
	fmt.Println("unset AWS_SESSION_TOKEN")
	fmt.Println("unset AWS_PROFILE")
	LogSuccess("AWS credentials cleared")
}

func getProfileNames(cfg *Config) []string {
	names := make([]string, 0, len(cfg.Profiles))
	for name := range cfg.Profiles {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

func outputCredentials(result *AuthResult, profileName, defaultRegion string) {
	if result.Credentials != nil {
		fmt.Printf("export AWS_ACCESS_KEY_ID='%s'\n", result.Credentials.AccessKeyID)
		fmt.Printf("export AWS_SECRET_ACCESS_KEY='%s'\n", result.Credentials.SecretAccessKey)
		if result.Credentials.SessionToken != "" {
			fmt.Printf("export AWS_SESSION_TOKEN='%s'\n", result.Credentials.SessionToken)
		} else {
			fmt.Println("unset AWS_SESSION_TOKEN")
		}
	} else {
		fmt.Println("unset AWS_ACCESS_KEY_ID")
		fmt.Println("unset AWS_SECRET_ACCESS_KEY")
		fmt.Println("unset AWS_SESSION_TOKEN")
	}

	if result.Credentials != nil {
		region := result.Region
		if region == "" {
			region = defaultRegion
		}
		if region != "" {
			fmt.Printf("export AWS_DEFAULT_REGION='%s'\n", region)
		}
	}

	fmt.Printf("export AWS_PROFILE='%s'\n", profileName)
}

func reportSuccess(profileName string, identity *Identity, remaining int64) {
	LogSuccess("Switched to %s (expires in %s)", profileName, formatDuration(remaining))
	LogVerbose("")
	LogVerbose("Authenticated as: %s", identity.ARN)
	LogVerbose("Account: %s", identity.Account)
}

func formatDuration(seconds int64) string {
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60

	if hours > 0 {
		return fmt.Sprintf("%dh %dm", hours, minutes)
	}
	return fmt.Sprintf("%dm", minutes)
}

func updateStarshipTimer(cfg *Config, profileName string, expirationEpoch int64) {
	if !cfg.Starship.Enabled {
		return
	}

	timerName := fmt.Sprintf("%s%s", cfg.Starship.TimerPrefix, profileName)
	RunCommand("starship-timer", "set", timerName, fmt.Sprintf("%d", expirationEpoch))
}
