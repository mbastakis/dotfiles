package cli

import (
	"context"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/yourusername/dotfiles/internal/tui"
)

func init() {
	rootCmd.AddCommand(statusCmd)
	rootCmd.AddCommand(syncCmd)
	rootCmd.AddCommand(tuiCmd)
	rootCmd.AddCommand(configCmd)
}

// statusCmd shows overall system status
var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show overall system status",
	Long:  "Display the current status of all enabled tools",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		
		fmt.Println("Dotfiles System Status")
		fmt.Println("======================")
		
		for _, tool := range registry.ListEnabled() {
			fmt.Printf("\n%s:\n", tool.Name())
			fmt.Println(strings.Repeat("-", len(tool.Name())+1))
			
			status, err := tool.Status(ctx)
			if err != nil {
				fmt.Printf("  Error: %v\n", err)
				continue
			}
			
			fmt.Printf("  Status: ")
			if status.Healthy {
				fmt.Println("✅ Healthy")
			} else {
				fmt.Println("❌ Unhealthy")
				if status.Error != nil {
					fmt.Printf("  Error: %v\n", status.Error)
				}
			}
			
			fmt.Printf("  Items: %d total", len(status.Items))
			
			var enabled, installed int
			for _, item := range status.Items {
				if item.Enabled {
					enabled++
				}
				if item.Installed {
					installed++
				}
			}
			
			fmt.Printf(", %d enabled, %d installed\n", enabled, installed)
		}
		
		return nil
	},
}

// syncCmd synchronizes all enabled tools
var syncCmd = &cobra.Command{
	Use:   "sync",
	Short: "Synchronize all enabled tools",
	Long:  "Run sync operation for all enabled tools in priority order",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		
		tools := registry.GetByPriority()
		if len(tools) == 0 {
			fmt.Println("No enabled tools found")
			return nil
		}
		
		fmt.Printf("Synchronizing %d tools...\n\n", len(tools))
		
		for _, tool := range tools {
			fmt.Printf("Syncing %s...\n", tool.Name())
			
			result, err := tool.Sync(ctx)
			if err != nil {
				fmt.Printf("❌ Failed to sync %s: %v\n", tool.Name(), err)
				continue
			}
			
			if result.Success {
				fmt.Printf("✅ %s synced successfully\n", tool.Name())
			} else {
				fmt.Printf("❌ %s sync failed: %s\n", tool.Name(), result.Message)
			}
			
			if len(result.Modified) > 0 {
				fmt.Printf("   Modified: %s\n", strings.Join(result.Modified, ", "))
			}
			
			fmt.Println()
		}
		
		fmt.Println("Sync complete!")
		return nil
	},
}

// tuiCmd launches the TUI interface
var tuiCmd = &cobra.Command{
	Use:   "tui",
	Short: "Launch interactive TUI interface",
	Long:  "Start the terminal user interface for interactive dotfiles management",
	RunE: func(cmd *cobra.Command, args []string) error {
		tuiApp := tui.NewTUI(cfg, registry)
		return tuiApp.Run()
	},
}

// configCmd manages configuration
var configCmd = &cobra.Command{
	Use:   "config",
	Short: "Manage configuration",
	Long:  "Commands for managing dotfiles configuration",
}

func init() {
	configCmd.AddCommand(configValidateCmd)
	configCmd.AddCommand(configShowCmd)
}

var configValidateCmd = &cobra.Command{
	Use:   "validate",
	Short: "Validate configuration",
	Long:  "Check if the current configuration is valid",
	RunE: func(cmd *cobra.Command, args []string) error {
		if err := cfg.Validate(); err != nil {
			fmt.Printf("❌ Configuration is invalid: %v\n", err)
			return err
		}
		
		fmt.Println("✅ Configuration is valid")
		return nil
	},
}

var configShowCmd = &cobra.Command{
	Use:   "show",
	Short: "Show current configuration",
	Long:  "Display the current configuration with resolved variables",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Printf("Configuration file: %s\n", cfgFile)
		fmt.Printf("Dotfiles path: %s\n", cfg.Global.DotfilesPath)
		fmt.Printf("Log level: %s\n", cfg.Global.LogLevel)
		fmt.Printf("Dry run: %t\n", cfg.Global.DryRun)
		fmt.Printf("Auto confirm: %t\n", cfg.Global.AutoConfirm)
		fmt.Printf("Backup enabled: %t\n", cfg.Global.BackupEnabled)
		
		if cfg.Global.BackupEnabled {
			fmt.Printf("Backup suffix: %s\n", cfg.Global.BackupSuffix)
		}
		
		fmt.Printf("\nEnabled tools:\n")
		for _, tool := range registry.ListEnabled() {
			fmt.Printf("  - %s (priority %d)\n", tool.Name(), tool.Priority())
		}
		
		return nil
	},
}