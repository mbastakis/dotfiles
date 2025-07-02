package cli

import (
	"context"
	"fmt"
	"log/slog"
	"os"

	"github.com/mbastakis/dotfiles/internal/common"
	"github.com/mbastakis/dotfiles/internal/config"
	"github.com/mbastakis/dotfiles/internal/perf"
	"github.com/mbastakis/dotfiles/internal/tools"
	"github.com/mbastakis/dotfiles/internal/tools/apps"
	"github.com/mbastakis/dotfiles/internal/tools/homebrew"
	"github.com/mbastakis/dotfiles/internal/tools/npm"
	"github.com/mbastakis/dotfiles/internal/tools/rsync"
	"github.com/mbastakis/dotfiles/internal/tools/stow"
	"github.com/mbastakis/dotfiles/internal/tools/uv"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	cfgFile  string
	cfg      *config.Config
	registry *tools.ToolRegistry
)

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "dotfiles",
	Short: "Modern TUI dotfiles manager",
	Long: `A modern, interactive CLI tool for managing your dotfiles with ease.
Built with Go and featuring a beautiful TUI interface powered by Bubbletea.

Features:
- 🖥️  Dual Interface: Use as CLI tool or interactive TUI
- 📦 Smart Package Management: Leverage GNU Stow with intelligent conflict resolution
- 🎨 Themeable: Customize the interface to match your style
- ⚡ Fast & Reliable: Written in Go for performance and reliability`,
	PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
		return initConfig()
	},
}

// Execute adds all child commands to the root command and sets flags appropriately.
func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func init() {
	// Global flags
	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is ~/.config/dotfiles/config.yaml)")
	rootCmd.PersistentFlags().Bool("dry-run", false, "show what would be done without executing")
	rootCmd.PersistentFlags().Bool("verbose", false, "enable verbose output")
	rootCmd.PersistentFlags().Bool("yes", false, "answer yes to all prompts")
	rootCmd.PersistentFlags().Bool("no-color", false, "disable colored output")

	// Bind flags to viper
	viper.BindPFlag("global.dry_run", rootCmd.PersistentFlags().Lookup("dry-run"))
	viper.BindPFlag("global.verbose", rootCmd.PersistentFlags().Lookup("verbose"))
	viper.BindPFlag("global.auto_confirm", rootCmd.PersistentFlags().Lookup("yes"))
	viper.BindPFlag("global.no_color", rootCmd.PersistentFlags().Lookup("no-color"))

	// Register tool commands statically
	registerToolCommands()
}

// initConfig reads in config file and ENV variables
func initConfig() error {
	if cfgFile != "" {
		viper.SetConfigFile(cfgFile)
	} else {
		home, err := os.UserHomeDir()
		cobra.CheckErr(err)

		// Search config in ~/.config/dotfiles directory
		viper.AddConfigPath(home + "/.config/dotfiles")
		viper.SetConfigType("yaml")
		viper.SetConfigName("config")
	}

	viper.AutomaticEnv() // read in environment variables that match

	// Load configuration
	var err error
	configPath := cfgFile
	if configPath == "" {
		home, _ := os.UserHomeDir()
		configPath = home + "/.config/dotfiles/config.yaml"
	}

	cfg, err = config.Load(configPath)
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}

	// Override config with CLI flags and env vars
	if viper.IsSet("global.dry_run") {
		cfg.Global.DryRun = viper.GetBool("global.dry_run")
	}
	if viper.IsSet("global.auto_confirm") {
		cfg.Global.AutoConfirm = viper.GetBool("global.auto_confirm")
	}
	if viper.IsSet("global.verbose") {
		cfg.Global.Verbose = viper.GetBool("global.verbose")
		// When verbose is enabled, set log level to debug
		if cfg.Global.Verbose {
			cfg.Global.LogLevel = "debug"
		}
	}

	// Initialize logger based on configuration
	var logLevel slog.Level
	switch cfg.Global.LogLevel {
	case "debug":
		logLevel = slog.LevelDebug
	case "info":
		logLevel = slog.LevelInfo
	case "warn":
		logLevel = slog.LevelWarn
	case "error":
		logLevel = slog.LevelError
	default:
		logLevel = slog.LevelInfo
	}
	common.InitLogger(logLevel, cfg.Global.Verbose)

	// Expand environment variables in config
	if err := cfg.ExpandVariables(); err != nil {
		return fmt.Errorf("failed to expand variables: %w", err)
	}

	// Validate configuration
	if err := cfg.Validate(); err != nil {
		return fmt.Errorf("invalid configuration: %w", err)
	}

	// Initialize performance systems from configuration
	ctx := context.Background()
	if err := perf.InitGlobalCaches(ctx, cfg); err != nil {
		return fmt.Errorf("failed to initialize caches: %w", err)
	}

	if err := perf.InitGlobalMonitor(cfg); err != nil {
		return fmt.Errorf("failed to initialize monitor: %w", err)
	}

	if err := perf.InitGlobalProfiler(cfg); err != nil {
		return fmt.Errorf("failed to initialize profiler: %w", err)
	}

	// Start performance monitoring
	perf.StartGlobalMonitor(ctx)
	perf.StartGlobalProfiling(ctx)

	// Initialize tool registry
	registry = tools.NewToolRegistry()

	// Register all tools
	stowTool := stow.NewStowTool(cfg)
	if err := registry.Register(stowTool); err != nil {
		return fmt.Errorf("failed to register stow tool: %w", err)
	}

	rsyncTool := rsync.NewRsyncTool(cfg)
	if err := registry.Register(rsyncTool); err != nil {
		return fmt.Errorf("failed to register rsync tool: %w", err)
	}

	homebrewTool := homebrew.NewHomebrewTool(cfg)
	if err := registry.Register(homebrewTool); err != nil {
		return fmt.Errorf("failed to register homebrew tool: %w", err)
	}

	npmTool := npm.NewNPMTool(cfg)
	if err := registry.Register(npmTool); err != nil {
		return fmt.Errorf("failed to register npm tool: %w", err)
	}

	uvTool := uv.NewUVTool(cfg)
	if err := registry.Register(uvTool); err != nil {
		return fmt.Errorf("failed to register uv tool: %w", err)
	}

	appsTool := apps.NewAppsTool(cfg)
	if err := registry.Register(appsTool); err != nil {
		return fmt.Errorf("failed to register apps tool: %w", err)
	}

	return nil
}

// registerToolCommands registers all known tool commands statically
func registerToolCommands() {
	// List of all known tools
	toolNames := []string{"stow", "rsync", "homebrew", "npm", "uv", "apps"}

	for _, toolName := range toolNames {
		toolCmd := createLazyToolCommand(toolName)
		rootCmd.AddCommand(toolCmd)
	}
}

// createLazyToolCommand creates a command for a tool that loads config lazily
func createLazyToolCommand(toolName string) *cobra.Command {
	toolCmd := &cobra.Command{
		Use:   toolName,
		Short: fmt.Sprintf("Manage %s operations", toolName),
		Long:  fmt.Sprintf("Commands for managing %s tool operations", toolName),
		PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
			// Ensure config is loaded
			if cfg == nil || registry == nil {
				if err := initConfig(); err != nil {
					return fmt.Errorf("failed to initialize configuration: %w", err)
				}
			}
			return nil
		},
		ValidArgsFunction: func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
			// Completion for tool subcommands
			subcommands := []string{"status", "list", "install", "update", "remove", "sync"}
			if toolName == "homebrew" {
				subcommands = append(subcommands, "list-packages", "install-package", "status-package")
			}
			return subcommands, cobra.ShellCompDirectiveNoFileComp
		},
	}

	// Add common subcommands for each tool
	toolCmd.AddCommand(&cobra.Command{
		Use:   "status",
		Short: fmt.Sprintf("Show %s status", toolName),
		Run:   func(cmd *cobra.Command, args []string) { fmt.Printf("Status for %s\n", toolName) },
	})
	toolCmd.AddCommand(&cobra.Command{
		Use:   "list",
		Short: fmt.Sprintf("List %s items", toolName),
		Run:   func(cmd *cobra.Command, args []string) { fmt.Printf("List for %s\n", toolName) },
	})
	toolCmd.AddCommand(&cobra.Command{
		Use:   "sync",
		Short: fmt.Sprintf("Sync %s", toolName),
		Run:   func(cmd *cobra.Command, args []string) { fmt.Printf("Sync for %s\n", toolName) },
	})

	return toolCmd
}

// GetConfig returns the current configuration
func GetConfig() *config.Config {
	return cfg
}

// GetRegistry returns the tool registry
func GetRegistry() *tools.ToolRegistry {
	return registry
}
