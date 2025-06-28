package cli

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"github.com/yourusername/dotfiles/internal/config"
	"github.com/yourusername/dotfiles/internal/tools"
	"github.com/yourusername/dotfiles/internal/tools/apps"
	"github.com/yourusername/dotfiles/internal/tools/homebrew"
	"github.com/yourusername/dotfiles/internal/tools/npm"
	"github.com/yourusername/dotfiles/internal/tools/rsync"
	"github.com/yourusername/dotfiles/internal/tools/stow"
	"github.com/yourusername/dotfiles/internal/tools/uv"
)

var (
	cfgFile string
	cfg     *config.Config
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
		if err := initConfig(); err != nil {
			return err
		}
		// Add tool commands after config is loaded
		if registry != nil && !commandsAdded {
			for _, tool := range registry.List() {
				// Check if command already exists
				exists := false
				for _, existing := range cmd.Root().Commands() {
					if existing.Name() == tool.Name() {
						exists = true
						break
					}
				}
				if !exists {
					toolCmd := createToolCommand(tool)
					cmd.Root().AddCommand(toolCmd)
				}
			}
			commandsAdded = true
		}
		return nil
	},
}

// Execute adds all child commands to the root command and sets flags appropriately.
func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

// commandsAdded tracks if dynamic commands have been added
var commandsAdded bool

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

	// Expand environment variables in config
	if err := cfg.ExpandVariables(); err != nil {
		return fmt.Errorf("failed to expand variables: %w", err)
	}

	// Validate configuration
	if err := cfg.Validate(); err != nil {
		return fmt.Errorf("invalid configuration: %w", err)
	}

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

// createToolCommand creates a command for a specific tool
func createToolCommand(tool tools.Tool) *cobra.Command {
	toolCmd := &cobra.Command{
		Use:   tool.Name(),
		Short: fmt.Sprintf("Manage %s operations", tool.Name()),
		Long:  fmt.Sprintf("Commands for managing %s tool operations", tool.Name()),
	}

	// Add common subcommands for each tool
	toolCmd.AddCommand(createStatusCommand(tool))
	toolCmd.AddCommand(createListCommand(tool))
	toolCmd.AddCommand(createInstallCommand(tool))
	toolCmd.AddCommand(createUpdateCommand(tool))
	toolCmd.AddCommand(createRemoveCommand(tool))
	toolCmd.AddCommand(createSyncCommand(tool))

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