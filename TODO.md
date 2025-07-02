#TODO: Themes don't change the UI
- Investigate the issue and identify the root cause
- Implement a fix for the theme switching functionality
- Test the fix to ensure it works as expected
- Update any relevant documentation
- Use snaphappy and target the Ghostty terminal that is running the doti tool to capture screenshots of the UI before and after the fix

#TODO: config.go while we have config/dotfiles/config.yaml is confusing

#TODO: Check entire repo, for inconsistencies
- I want consistent logging across the entire repo and all tools
  - Currently some tools like `dot apps sync` and `dot homebrew sync` and `dot stow sync` etc log in different levels and with different formats
  - I want to have a consistent logging format and level across all tools
- I want consistent error handling across the entire repo and all tools
- I want consistent shortcuts in the TUI views
  - Currently some tui views have different shortcuts for the same actions
  - Some shortcuts are global like "s" which brings you to the Status View no matter where you are, this is not correct. "s" should only be used in the main menu because "s" in the stow tool for example should sync all. Rethink the shortcuts and make the text in the footer section of the TUI views more consistent and with less text, only when you do "?" it should show the full list of shortcuts
- I want consistent error messages across the entire repo and all tools

#TODO: make `ctrl + r` in the terminal trigger atuin not zsh history search
