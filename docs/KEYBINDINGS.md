# Dotfiles TUI Keybindings Reference

## Overview

This document describes the standardized keybinding system implemented in the Dotfiles TUI application. All tools and screens follow consistent keybinding patterns for better user experience.

## Global Navigation

| Key | Action | Context |
|-----|--------|---------|
| `↑` / `k` | Move up | List navigation |
| `↓` / `j` | Move down | List navigation |
| `Enter` | Select/Confirm | Menu selection only |
| `q` / `Esc` | Go back / Quit | All screens |
| `Tab` | Next field | Forms |
| `Ctrl+C` | Force quit | Emergency exit |

## Tool Operations

These keybindings are consistent across all tool screens (Stow, Homebrew, NPM, etc.):

| Key | Action | Description |
|-----|--------|-------------|
| `i` | Install | Install selected item(s) |
| `u` | Update | Update selected item(s) |
| `d` | Delete/Remove | Remove selected item(s) |
| `s` | Sync | Sync all enabled items |
| `r` | Refresh | Refresh tool status |
| `Space` / `x` | Toggle selection | Select/deselect items for batch operations |
| `?` | Help | Show extended help |

## Screen-Specific Keybindings

### Main Menu
- `Enter` - Navigate to selected tool/screen
- `s` - Show system status
- `q` - Quit application

### Overview Screen
- `r` - Refresh system status
- `↑/↓` - Navigate table
- `q/Esc` - Back to main menu

### Settings Screen
- `Enter` - Edit selected setting
- `r` - Reset to default value
- `y/n` - Set boolean values
- `1-9` - Select enum options
- `Esc` - Cancel editing

### Themes Screen
- `Enter` - Apply selected theme
- `↑/↓` - Navigate themes
- `q/Esc` - Back to main menu

## Implementation Details

### Keybinding Architecture

1. **Centralized Definitions**: All keybindings are defined in `internal/tui/keys/bindings.go`
2. **Tool Consistency**: The `ToolKeyMap` ensures all tools use the same keys for operations
3. **Navigation Consistency**: The `NavigationKeyMap` provides standard navigation keys
4. **Context Awareness**: Footer help text updates based on current screen state

### Key Features

1. **No Conflicts**: Enter key is reserved for navigation in lists, not for tool operations
2. **Visual Feedback**: Footer always shows available keybindings
3. **Help System**: Press `?` for extended help on any tool screen
4. **State Awareness**: Keybindings are disabled during loading states

### Best Practices

1. **Always show context**: The footer should display relevant keybindings
2. **Disable during operations**: Keys should not respond during async operations
3. **Clear visual feedback**: Selected items should be clearly indicated
4. **Consistent patterns**: Similar operations use the same keys across all tools

## Troubleshooting

If keybindings are not working as expected:

1. Check if an operation is in progress (loading state)
2. Ensure you have items selected for item-specific operations
3. Verify you're in the correct screen context
4. Check the footer for available operations

## Future Enhancements

- Multi-select support with Space/x key
- Vim-style visual mode for batch operations
- Customizable keybindings via configuration
- Keyboard shortcut cheat sheet overlay