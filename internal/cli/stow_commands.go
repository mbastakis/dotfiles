package cli

import (
	"context"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
)

// func init() {
//	rootCmd.AddCommand(stowCmd)
// }

// stowCmd represents the stow command
var stowCmd = &cobra.Command{
	Use:   "stow",
	Short: "Manage stow operations",
	Long:  "Commands for managing GNU stow package operations",
}

func init() {
	stowCmd.AddCommand(stowStatusCmd)
	stowCmd.AddCommand(stowListCmd)
	stowCmd.AddCommand(stowLinkCmd)
	stowCmd.AddCommand(stowUnlinkCmd)
	stowCmd.AddCommand(stowSyncCmd)
}

var stowStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show stow status",
	Long:  "Display the current status of stow packages",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		
		if registry == nil {
			return fmt.Errorf("tool registry not initialized")
		}
		
		tool, exists := registry.Get("stow")
		if !exists {
			return fmt.Errorf("stow tool not found")
		}
		
		status, err := tool.Status(ctx)
		if err != nil {
			return fmt.Errorf("failed to get stow status: %w", err)
		}

		printStatus(status)
		return nil
	},
}

var stowListCmd = &cobra.Command{
	Use:   "list",
	Short: "List stow packages",
	Long:  "List all stow packages and their status",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		
		if registry == nil {
			return fmt.Errorf("tool registry not initialized")
		}
		
		tool, exists := registry.Get("stow")
		if !exists {
			return fmt.Errorf("stow tool not found")
		}
		
		items, err := tool.List(ctx)
		if err != nil {
			return fmt.Errorf("failed to list stow packages: %w", err)
		}

		printItems(items)
		return nil
	},
}

var stowLinkCmd = &cobra.Command{
	Use:   "link [packages...]",
	Short: "Link stow packages",
	Long:  "Create symlinks for specified stow packages",
	Args:  cobra.MinimumNArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		
		if registry == nil {
			return fmt.Errorf("tool registry not initialized")
		}
		
		tool, exists := registry.Get("stow")
		if !exists {
			return fmt.Errorf("stow tool not found")
		}

		fmt.Printf("Linking stow packages: %s\n", strings.Join(args, ", "))
		
		result, err := tool.Install(ctx, args)
		if err != nil {
			return fmt.Errorf("failed to link stow packages: %w", err)
		}

		printResult(result)
		return nil
	},
}

var stowUnlinkCmd = &cobra.Command{
	Use:   "unlink [packages...]",
	Short: "Unlink stow packages",
	Long:  "Remove symlinks for specified stow packages",
	Args:  cobra.MinimumNArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		
		if registry == nil {
			return fmt.Errorf("tool registry not initialized")
		}
		
		tool, exists := registry.Get("stow")
		if !exists {
			return fmt.Errorf("stow tool not found")
		}

		// Confirm destructive operation unless --yes flag is set
		if cfg != nil && !cfg.Global.AutoConfirm {
			fmt.Printf("This will unlink stow packages: %s\n", strings.Join(args, ", "))
			fmt.Print("Are you sure? (y/N): ")
			
			var response string
			fmt.Scanln(&response)
			if strings.ToLower(response) != "y" && strings.ToLower(response) != "yes" {
				fmt.Println("Operation cancelled")
				return nil
			}
		}

		fmt.Printf("Unlinking stow packages: %s\n", strings.Join(args, ", "))
		
		result, err := tool.Remove(ctx, args)
		if err != nil {
			return fmt.Errorf("failed to unlink stow packages: %w", err)
		}

		printResult(result)
		return nil
	},
}

var stowSyncCmd = &cobra.Command{
	Use:   "sync",
	Short: "Sync all stow packages",
	Long:  "Synchronize all enabled stow packages",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		
		if registry == nil {
			return fmt.Errorf("tool registry not initialized")
		}
		
		tool, exists := registry.Get("stow")
		if !exists {
			return fmt.Errorf("stow tool not found")
		}
		
		fmt.Println("Synchronizing stow packages...")
		
		result, err := tool.Sync(ctx)
		if err != nil {
			return fmt.Errorf("failed to sync stow packages: %w", err)
		}

		printResult(result)
		return nil
	},
}