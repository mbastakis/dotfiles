package cli

import (
	"os"

	"github.com/spf13/cobra"
)

// completionCmd represents the completion command
var completionCmd = &cobra.Command{
	Use:   "completion [bash|zsh|fish|powershell]",
	Short: "Generate completion script for your shell",
	Long: `Generate completion script for your shell to enable tab-completion for the dotfiles command.

To load completions:

Bash:
  $ source <(dotfiles completion bash)
  
  # To load completions for each session, execute once:
  # Linux:
  $ dotfiles completion bash > /etc/bash_completion.d/dotfiles
  # macOS:
  $ dotfiles completion bash > /usr/local/etc/bash_completion.d/dotfiles

Zsh:
  # If shell completion is not already enabled in your environment,
  # you will need to enable it. You can execute the following once:
  $ echo "autoload -U compinit; compinit" >> ~/.zshrc
  
  # To load completions for each session, execute once:
  $ dotfiles completion zsh > "${fpath[1]}/_dotfiles"
  
  # You will need to start a new shell for this setup to take effect.

Fish:
  $ dotfiles completion fish | source
  
  # To load completions for each session, execute once:
  $ dotfiles completion fish > ~/.config/fish/completions/dotfiles.fish

PowerShell:
  PS> dotfiles completion powershell | Out-String | Invoke-Expression
  
  # To load completions for every new session, run:
  PS> dotfiles completion powershell > dotfiles.ps1
  # and source this file from your PowerShell profile.
`,
	DisableFlagsInUseLine: true,
	ValidArgs:             []string{"bash", "zsh", "fish", "powershell"},
	Args:                  cobra.MatchAll(cobra.ExactArgs(1), cobra.OnlyValidArgs),
	Run: func(cmd *cobra.Command, args []string) {
		switch args[0] {
		case "bash":
			cmd.Root().GenBashCompletion(os.Stdout)
		case "zsh":
			cmd.Root().GenZshCompletion(os.Stdout)
		case "fish":
			cmd.Root().GenFishCompletion(os.Stdout, true)
		case "powershell":
			cmd.Root().GenPowerShellCompletion(os.Stdout)
		}
	},
}

// setupCompletions configures custom completion functions for commands
func setupCompletions() {
	// Set up completion for root command
	rootCmd.ValidArgsFunction = func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
		commands := []string{"status", "sync", "tui", "config", "completion"}
		commands = append(commands, getToolNames()...)
		return commands, cobra.ShellCompDirectiveNoFileComp
	}
}

// getToolNames returns a list of all available tool names for completion
func getToolNames() []string {
	return []string{"stow", "rsync", "homebrew", "npm", "uv", "apps"}
}

// getToolSubcommands returns common subcommands for tools
func getToolSubcommands() []string {
	return []string{"status", "list", "install", "update", "remove", "sync"}
}

// getHomebrewCategories returns homebrew package categories for completion
func getHomebrewCategories() []string {
	return []string{"formulae", "casks", "taps"}
}

// getToolItemsCompletion returns completion function for tool items
func getToolItemsCompletion(toolName string) func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
	return func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
		// Return empty for now - would need to query actual tool items at runtime
		// This is a placeholder for dynamic completion based on actual tool state
		return []string{}, cobra.ShellCompDirectiveNoFileComp
	}
}

// getStowPackagesCompletion returns completion function for stow packages
func getStowPackagesCompletion() func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
	return func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
		// Return common stow package names as static examples
		packages := []string{"shell", "config", "git", "vim", "nvim", "tmux", "zsh"}
		return packages, cobra.ShellCompDirectiveNoFileComp
	}
}

// getHomebrewCategoryCompletion returns completion function for homebrew categories
func getHomebrewCategoryCompletion() func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
	return func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
		return getHomebrewCategories(), cobra.ShellCompDirectiveNoFileComp
	}
}

func init() {
	rootCmd.AddCommand(completionCmd)
	setupCompletions()
}