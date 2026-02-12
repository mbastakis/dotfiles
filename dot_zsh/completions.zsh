#!/usr/bin/env zsh
# completions.zsh - Tool completions
# Loaded AFTER compinit (which runs in plugins.zsh)
#
# Most completions are now managed via carapace specs:
#   ~/.config/carapace/specs/
#
# To add/update completions for tools not in carapace-bin's 669 built-in completers:
#   carapace-sync --add <tool>    # Add new tool
#   carapace-sync                 # Sync all (updates on version change)
#   carapace-sync --force         # Force regenerate all specs
#   carapace-sync --list          # Show managed tools
#
# Managed tools: bw, opencode, obsidian-cli, chezmoi, bun
# See: ~/.config/carapace/tools.yaml

# No runtime completion generation needed - carapace handles everything via specs

# Ensure chezmoi completion is registered even before carapace cache refresh
if (( ${+functions[_carapace_completer]} )) && command -v chezmoi &>/dev/null; then
  compdef _carapace_completer chezmoi
fi
