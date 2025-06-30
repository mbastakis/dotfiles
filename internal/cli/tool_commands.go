package cli

import (
	"context"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/yourusername/dotfiles/internal/tools"
)

// createStatusCommand creates a status command for a tool
func createStatusCommand(tool tools.Tool) *cobra.Command {
	return &cobra.Command{
		Use:   "status",
		Short: fmt.Sprintf("Show %s status", tool.Name()),
		Long:  fmt.Sprintf("Display the current status of %s tool", tool.Name()),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			status, err := tool.Status(ctx)
			if err != nil {
				return fmt.Errorf("failed to get %s status: %w", tool.Name(), err)
			}

			printStatus(status)
			return nil
		},
	}
}

// createListCommand creates a list command for a tool
func createListCommand(tool tools.Tool) *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: fmt.Sprintf("List %s items", tool.Name()),
		Long:  fmt.Sprintf("List all items managed by %s tool", tool.Name()),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			items, err := tool.List(ctx)
			if err != nil {
				return fmt.Errorf("failed to list %s items: %w", tool.Name(), err)
			}

			printItems(items)
			return nil
		},
	}
}

// createInstallCommand creates an install command for a tool
func createInstallCommand(tool tools.Tool) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "install [items...]",
		Short: fmt.Sprintf("Install %s items", tool.Name()),
		Long:  fmt.Sprintf("Install specified items using %s tool", tool.Name()),
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			
			// Check for --all flag
			if all, _ := cmd.Flags().GetBool("all"); all {
				// Get all available items and install enabled ones
				items, err := tool.List(ctx)
				if err != nil {
					return fmt.Errorf("failed to list %s items: %w", tool.Name(), err)
				}
				
				var enabledItems []string
				for _, item := range items {
					if item.Enabled {
						enabledItems = append(enabledItems, item.Name)
					}
				}
				args = enabledItems
			}

			if len(args) == 0 {
				return fmt.Errorf("no items to install")
			}

			fmt.Printf("Installing %s items: %s\n", tool.Name(), strings.Join(args, ", "))
			
			result, err := tool.Install(ctx, args)
			if err != nil {
				return fmt.Errorf("failed to install %s items: %w", tool.Name(), err)
			}

			printResult(result)
			return nil
		},
	}

	// Add tool-specific flags
	cmd.Flags().Bool("all", false, "install all enabled items")
	
	// Add tool-specific flags based on tool type
	switch tool.Name() {
	case "stow":
		cmd.Use = "link [packages...]"
		cmd.Short = "Link stow packages"
		cmd.Long = "Create symlinks for specified stow packages"
		cmd.Flags().StringSlice("packages", nil, "specific packages to link")
	case "homebrew":
		cmd.Flags().StringSlice("category", nil, "homebrew categories to install (core, apps, dev, mas)")
	case "npm":
		cmd.Flags().StringSlice("packages", nil, "specific npm packages to install")
	case "uv":
		cmd.Flags().StringSlice("packages", nil, "specific uv packages to install")
	}

	return cmd
}

// createUpdateCommand creates an update command for a tool
func createUpdateCommand(tool tools.Tool) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "update [items...]",
		Short: fmt.Sprintf("Update %s items", tool.Name()),
		Long:  fmt.Sprintf("Update specified items using %s tool", tool.Name()),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			
			// If no specific items provided, update all
			if len(args) == 0 {
				items, err := tool.List(ctx)
				if err != nil {
					return fmt.Errorf("failed to list %s items: %w", tool.Name(), err)
				}
				
				for _, item := range items {
					if item.Enabled && item.Installed {
						args = append(args, item.Name)
					}
				}
			}

			if len(args) == 0 {
				fmt.Printf("No %s items to update\n", tool.Name())
				return nil
			}

			fmt.Printf("Updating %s items: %s\n", tool.Name(), strings.Join(args, ", "))
			
			result, err := tool.Update(ctx, args)
			if err != nil {
				return fmt.Errorf("failed to update %s items: %w", tool.Name(), err)
			}

			printResult(result)
			return nil
		},
	}

	// Tool-specific customizations
	switch tool.Name() {
	case "stow":
		cmd.Use = "relink [packages...]"
		cmd.Short = "Re-link stow packages"
		cmd.Long = "Unlink and re-link specified stow packages"
	}

	return cmd
}

// createRemoveCommand creates a remove command for a tool
func createRemoveCommand(tool tools.Tool) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "remove [items...]",
		Short: fmt.Sprintf("Remove %s items", tool.Name()),
		Long:  fmt.Sprintf("Remove specified items using %s tool", tool.Name()),
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			
			// Confirm destructive operation unless --yes flag is set
			if !cfg.Global.AutoConfirm {
				fmt.Printf("This will remove %s items: %s\n", tool.Name(), strings.Join(args, ", "))
				fmt.Print("Are you sure? (y/N): ")
				
				var response string
				fmt.Scanln(&response)
				if strings.ToLower(response) != "y" && strings.ToLower(response) != "yes" {
					fmt.Println("Operation cancelled")
					return nil
				}
			}

			fmt.Printf("Removing %s items: %s\n", tool.Name(), strings.Join(args, ", "))
			
			result, err := tool.Remove(ctx, args)
			if err != nil {
				return fmt.Errorf("failed to remove %s items: %w", tool.Name(), err)
			}

			printResult(result)
			return nil
		},
	}

	// Tool-specific customizations
	switch tool.Name() {
	case "stow":
		cmd.Use = "unlink [packages...]"
		cmd.Short = "Unlink stow packages"
		cmd.Long = "Remove symlinks for specified stow packages"
	}

	return cmd
}

// createSyncCommand creates a sync command for a tool
func createSyncCommand(tool tools.Tool) *cobra.Command {
	return &cobra.Command{
		Use:   "sync",
		Short: fmt.Sprintf("Sync all %s items", tool.Name()),
		Long:  fmt.Sprintf("Synchronize all enabled %s items", tool.Name()),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			
			fmt.Printf("Synchronizing %s...\n", tool.Name())
			
			result, err := tool.Sync(ctx)
			if err != nil {
				return fmt.Errorf("failed to sync %s: %w", tool.Name(), err)
			}

			printResult(result)
			return nil
		},
	}
}

// Helper function to get tool from registry by name
func getTool(toolName string) (tools.Tool, error) {
	if registry == nil {
		return nil, fmt.Errorf("registry not initialized")
	}
	
	tool, exists := registry.Get(toolName)
	if !exists {
		return nil, fmt.Errorf("tool %s not found or not enabled", toolName)
	}
	
	return tool, nil
}

// Lazy command functions that load tools from registry when executed

// createLazyStatusCommand creates a status command for a tool by name
func createLazyStatusCommand(toolName string) *cobra.Command {
	return &cobra.Command{
		Use:   "status",
		Short: fmt.Sprintf("Show %s status", toolName),
		Long:  fmt.Sprintf("Display the current status of %s tool", toolName),
		RunE: func(cmd *cobra.Command, args []string) error {
			tool, err := getTool(toolName)
			if err != nil {
				return err
			}
			
			ctx := context.Background()
			status, err := tool.Status(ctx)
			if err != nil {
				return fmt.Errorf("failed to get %s status: %w", tool.Name(), err)
			}

			printStatus(status)
			return nil
		},
	}
}

// createLazyListCommand creates a list command for a tool by name
func createLazyListCommand(toolName string) *cobra.Command {
	return &cobra.Command{
		Use:   "list",
		Short: fmt.Sprintf("List %s items", toolName),
		Long:  fmt.Sprintf("List all items managed by %s tool", toolName),
		RunE: func(cmd *cobra.Command, args []string) error {
			tool, err := getTool(toolName)
			if err != nil {
				return err
			}
			
			ctx := context.Background()
			items, err := tool.List(ctx)
			if err != nil {
				return fmt.Errorf("failed to list %s items: %w", tool.Name(), err)
			}

			printItems(items)
			return nil
		},
	}
}

// createLazyInstallCommand creates an install command for a tool by name
func createLazyInstallCommand(toolName string) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "install [items...]",
		Short: fmt.Sprintf("Install %s items", toolName),
		Long:  fmt.Sprintf("Install specified items using %s tool", toolName),
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			tool, err := getTool(toolName)
			if err != nil {
				return err
			}
			
			ctx := context.Background()
			
			// Check for --all flag
			if all, _ := cmd.Flags().GetBool("all"); all {
				// Get all available items and install enabled ones
				items, err := tool.List(ctx)
				if err != nil {
					return fmt.Errorf("failed to list %s items: %w", tool.Name(), err)
				}
				
				var enabledItems []string
				for _, item := range items {
					if item.Enabled {
						enabledItems = append(enabledItems, item.Name)
					}
				}
				args = enabledItems
			}

			if len(args) == 0 {
				return fmt.Errorf("no items to install")
			}

			fmt.Printf("Installing %s items: %s\n", tool.Name(), strings.Join(args, ", "))
			
			result, err := tool.Install(ctx, args)
			if err != nil {
				return fmt.Errorf("failed to install %s items: %w", tool.Name(), err)
			}

			printResult(result)
			return nil
		},
	}

	// Add tool-specific flags
	cmd.Flags().Bool("all", false, "install all enabled items")
	
	// Add tool-specific flags based on tool type
	switch toolName {
	case "stow":
		cmd.Use = "link [packages...]"
		cmd.Short = "Link stow packages"
		cmd.Long = "Create symlinks for specified stow packages"
		cmd.Flags().StringSlice("packages", nil, "specific packages to link")
	case "homebrew":
		cmd.Flags().StringSlice("category", nil, "homebrew categories to install (core, apps, dev, mas)")
	case "npm":
		cmd.Flags().StringSlice("packages", nil, "specific npm packages to install")
	case "uv":
		cmd.Flags().StringSlice("packages", nil, "specific uv packages to install")
	}

	return cmd
}

// createLazyUpdateCommand creates an update command for a tool by name
func createLazyUpdateCommand(toolName string) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "update [items...]",
		Short: fmt.Sprintf("Update %s items", toolName),
		Long:  fmt.Sprintf("Update specified items using %s tool", toolName),
		RunE: func(cmd *cobra.Command, args []string) error {
			tool, err := getTool(toolName)
			if err != nil {
				return err
			}
			
			ctx := context.Background()
			
			// If no specific items provided, update all
			if len(args) == 0 {
				items, err := tool.List(ctx)
				if err != nil {
					return fmt.Errorf("failed to list %s items: %w", tool.Name(), err)
				}
				
				for _, item := range items {
					if item.Enabled && item.Installed {
						args = append(args, item.Name)
					}
				}
			}

			if len(args) == 0 {
				fmt.Printf("No %s items to update\n", tool.Name())
				return nil
			}

			fmt.Printf("Updating %s items: %s\n", tool.Name(), strings.Join(args, ", "))
			
			result, err := tool.Update(ctx, args)
			if err != nil {
				return fmt.Errorf("failed to update %s items: %w", tool.Name(), err)
			}

			printResult(result)
			return nil
		},
	}

	// Tool-specific customizations
	switch toolName {
	case "stow":
		cmd.Use = "relink [packages...]"
		cmd.Short = "Re-link stow packages"
		cmd.Long = "Unlink and re-link specified stow packages"
	}

	return cmd
}

// createLazyRemoveCommand creates a remove command for a tool by name
func createLazyRemoveCommand(toolName string) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "remove [items...]",
		Short: fmt.Sprintf("Remove %s items", toolName),
		Long:  fmt.Sprintf("Remove specified items using %s tool", toolName),
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			tool, err := getTool(toolName)
			if err != nil {
				return err
			}
			
			ctx := context.Background()
			
			// Confirm destructive operation unless --yes flag is set
			if !cfg.Global.AutoConfirm {
				fmt.Printf("This will remove %s items: %s\n", tool.Name(), strings.Join(args, ", "))
				fmt.Print("Are you sure? (y/N): ")
				
				var response string
				fmt.Scanln(&response)
				if strings.ToLower(response) != "y" && strings.ToLower(response) != "yes" {
					fmt.Println("Operation cancelled")
					return nil
				}
			}

			fmt.Printf("Removing %s items: %s\n", tool.Name(), strings.Join(args, ", "))
			
			result, err := tool.Remove(ctx, args)
			if err != nil {
				return fmt.Errorf("failed to remove %s items: %w", tool.Name(), err)
			}

			printResult(result)
			return nil
		},
	}

	// Tool-specific customizations
	switch toolName {
	case "stow":
		cmd.Use = "unlink [packages...]"
		cmd.Short = "Unlink stow packages"
		cmd.Long = "Remove symlinks for specified stow packages"
	}

	return cmd
}

// createLazySyncCommand creates a sync command for a tool by name
func createLazySyncCommand(toolName string) *cobra.Command {
	return &cobra.Command{
		Use:   "sync",
		Short: fmt.Sprintf("Sync all %s items", toolName),
		Long:  fmt.Sprintf("Synchronize all enabled %s items", toolName),
		RunE: func(cmd *cobra.Command, args []string) error {
			tool, err := getTool(toolName)
			if err != nil {
				return err
			}
			
			ctx := context.Background()
			
			fmt.Printf("Synchronizing %s...\n", tool.Name())
			
			result, err := tool.Sync(ctx)
			if err != nil {
				return fmt.Errorf("failed to sync %s: %w", tool.Name(), err)
			}

			printResult(result)
			return nil
		},
	}
}

// createLazyListPackagesCommand creates a list-packages command for category tools
func createLazyListPackagesCommand(toolName string) *cobra.Command {
	return &cobra.Command{
		Use:   "list-packages <category>",
		Short: fmt.Sprintf("List %s packages in a category", toolName),
		Long:  fmt.Sprintf("List all packages in a specific %s category", toolName),
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			tool, err := getTool(toolName)
			if err != nil {
				return err
			}
			
			categoryTool, ok := tool.(tools.CategoryTool)
			if !ok || !categoryTool.SupportsCategories() {
				return fmt.Errorf("%s tool does not support categories", toolName)
			}
			
			ctx := context.Background()
			category := args[0]
			
			packages, err := categoryTool.ListCategoryItems(ctx, category)
			if err != nil {
				return fmt.Errorf("failed to list %s packages in category %s: %w", toolName, category, err)
			}

			fmt.Printf("%s packages in category '%s':\n", strings.Title(toolName), category)
			printItems(packages)
			return nil
		},
	}
}

// createLazyInstallPackageCommand creates an install-package command for category tools
func createLazyInstallPackageCommand(toolName string) *cobra.Command {
	return &cobra.Command{
		Use:   "install-package <category> <package>",
		Short: fmt.Sprintf("Install a specific %s package", toolName),
		Long:  fmt.Sprintf("Install a specific package from a %s category", toolName),
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			tool, err := getTool(toolName)
			if err != nil {
				return err
			}
			
			categoryTool, ok := tool.(tools.CategoryTool)
			if !ok || !categoryTool.SupportsCategories() {
				return fmt.Errorf("%s tool does not support categories", toolName)
			}
			
			ctx := context.Background()
			category := args[0]
			packageName := args[1]
			
			fmt.Printf("Installing %s package '%s' from category '%s'...\n", toolName, packageName, category)
			
			result, err := categoryTool.InstallCategoryItem(ctx, category, packageName)
			if err != nil {
				return fmt.Errorf("failed to install %s package %s: %w", toolName, packageName, err)
			}

			printResult(result)
			return nil
		},
	}
}

// createLazyStatusPackageCommand creates a status-package command for category tools
func createLazyStatusPackageCommand(toolName string) *cobra.Command {
	return &cobra.Command{
		Use:   "status-package <category> <package>",
		Short: fmt.Sprintf("Check status of a specific %s package", toolName),
		Long:  fmt.Sprintf("Check the installation status of a specific package from a %s category", toolName),
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			tool, err := getTool(toolName)
			if err != nil {
				return err
			}
			
			categoryTool, ok := tool.(tools.CategoryTool)
			if !ok || !categoryTool.SupportsCategories() {
				return fmt.Errorf("%s tool does not support categories", toolName)
			}
			
			ctx := context.Background()
			category := args[0]
			packageName := args[1]
			
			packages, err := categoryTool.ListCategoryItems(ctx, category)
			if err != nil {
				return fmt.Errorf("failed to list %s packages in category %s: %w", toolName, category, err)
			}

			// Find the specific package
			for _, pkg := range packages {
				if pkg.Name == packageName {
					fmt.Printf("Package '%s' in category '%s':\n", packageName, category)
					fmt.Printf("  Status: %s\n", pkg.Status)
					fmt.Printf("  Installed: %v\n", pkg.Installed)
					fmt.Printf("  Enabled: %v\n", pkg.Enabled)
					if pkg.Version != "" {
						fmt.Printf("  Version: %s\n", pkg.Version)
					}
					if pkg.Description != "" {
						fmt.Printf("  Description: %s\n", pkg.Description)
					}
					return nil
				}
			}
			
			return fmt.Errorf("package '%s' not found in category '%s'", packageName, category)
		},
	}
}