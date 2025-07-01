# Tmux Documentation

## Overview
Tmux (Terminal Multiplexer) is a powerful terminal management tool that allows you to create, access, and control multiple terminal sessions from a single window. It enables persistent sessions that survive network disconnections and provides advanced window/pane management capabilities.

## Key Concepts
- **Session**: A collection of windows managed by tmux (can be detached/reattached)
- **Window**: A full-screen terminal within a session (like tabs in a browser)
- **Pane**: A subdivision of a window (split horizontally or vertically)
- **Prefix Key**: The key combination (default: Ctrl-b) that precedes tmux commands
- **Client**: The terminal instance connected to a tmux server

## Installation & Setup
```bash
# macOS (Homebrew)
brew install tmux

# Linux (Ubuntu/Debian)
sudo apt-get install tmux

# Linux (RHEL/CentOS)
sudo yum install tmux

# Verify installation
tmux -V
```

## Basic Usage
```bash
# Start new session
tmux
tmux new -s session-name

# List sessions
tmux ls
tmux list-sessions

# Attach to session
tmux attach -t session-name
tmux a -t session-name

# Detach from session
# Press: Ctrl-b d

# Kill session
tmux kill-session -t session-name

# Kill all sessions
tmux kill-server
```

## Common Patterns
### Session Management
```bash
# Create named session
tmux new -s work

# Create session in background
tmux new -s background -d

# Switch between sessions
# Press: Ctrl-b s (then select)

# Rename session
# Press: Ctrl-b $
```

### Window Management
```bash
# Create new window
# Press: Ctrl-b c

# Navigate windows
# Press: Ctrl-b n (next)
# Press: Ctrl-b p (previous)
# Press: Ctrl-b 0-9 (by number)

# Rename window
# Press: Ctrl-b ,

# Kill window
# Press: Ctrl-b &
```

### Pane Management
```bash
# Split horizontally
# Press: Ctrl-b %

# Split vertically
# Press: Ctrl-b "

# Navigate panes
# Press: Ctrl-b arrow-keys
# Press: Ctrl-b o (cycle)

# Resize panes
# Press: Ctrl-b Ctrl-arrow-keys

# Kill pane
# Press: Ctrl-b x

# Toggle pane zoom
# Press: Ctrl-b z
```

## Best Practices
- Use descriptive session names for easy identification
- Configure a custom prefix key if Ctrl-b conflicts with other tools
- Use pane synchronization for executing commands across multiple servers
- Set up a `.tmux.conf` file for persistent customization
- Use tmux plugins (via TPM - Tmux Plugin Manager) for enhanced functionality
- Create session scripts for complex workspace setups
- Use `tmux send-keys` for automation
- Enable mouse support for easier pane navigation and resizing

## Common Issues & Solutions
### Issue 1: Lost in Nested Tmux Sessions
**Problem**: Accidentally starting tmux inside tmux, causing prefix key conflicts
**Solution**: Check `$TMUX` environment variable before starting tmux, or use different prefix keys for nested sessions

### Issue 2: Copy/Paste Difficulties
**Problem**: System clipboard integration doesn't work as expected
**Solution**: 
- macOS: Use `reattach-to-user-namespace` or configure tmux-yank plugin
- Linux: Install xclip/xsel and configure tmux accordingly

### Issue 3: Color and Terminal Issues
**Problem**: Colors appear wrong or terminal features don't work
**Solution**: Set `export TERM=screen-256color` in shell or `set -g default-terminal "screen-256color"` in .tmux.conf

### Issue 4: SSH and Tmux Sessions
**Problem**: Tmux sessions die when SSH connection drops
**Solution**: This is actually tmux's strength - sessions persist! Just reconnect and reattach

### Issue 5: Configuration Not Loading
**Problem**: .tmux.conf changes don't take effect
**Solution**: Reload configuration with `tmux source-file ~/.tmux.conf` or restart tmux server

## Advanced Features
### Copy Mode
```bash
# Enter copy mode
# Press: Ctrl-b [

# Navigation in copy mode (vi-style)
# h,j,k,l - move cursor
# w,b - move by word
# / - search forward
# ? - search backward

# Start selection: Space
# Copy selection: Enter
# Paste: Ctrl-b ]
```

### Command Mode
```bash
# Enter command mode
# Press: Ctrl-b :

# Common commands
:new-window -n name
:split-window -h
:resize-pane -L 10
:set synchronize-panes on
```

### Useful Configuration (.tmux.conf)
```bash
# Change prefix key
set -g prefix C-a
unbind C-b

# Enable mouse
set -g mouse on

# Start windows/panes at 1
set -g base-index 1
setw -g pane-base-index 1

# Vi mode keys
setw -g mode-keys vi

# Faster key repetition
set -s escape-time 0

# Increase history
set -g history-limit 10000
```

## Resources
- [Official Tmux GitHub](https://github.com/tmux/tmux)
- [Tmux Cheat Sheet](https://tmuxcheatsheet.com/)
- [The Tao of Tmux (Free Book)](https://leanpub.com/the-tao-of-tmux/read)
- [Tmux Plugin Manager (TPM)](https://github.com/tmux-plugins/tpm)
- [Awesome Tmux Resources](https://github.com/rothgar/awesome-tmux)

## Terminal Emulation & ANSI/VT100 Control Sequences

Tmux works with terminal emulators that support ANSI/VT100 control sequences. Understanding these sequences helps troubleshoot display issues and understand how tmux communicates with terminals.

### VT100 Minimum Requirements

#### 1. Passive Display Requirements
To act as a basic display terminal, implement:
- **Cursor Movement**: `ESC[A` (up), `ESC[B` (down), `ESC[C` (right), `ESC[D` (left)
- **Cursor Positioning**: `ESC[H` (home), `ESC[24;80H` (position to line 24, column 80)
- **Screen Clearing**: `ESC[J` (clear to bottom), `ESC[K` (clear to end of line)
- **Character Attributes**: `ESC[0m` (normal), `ESC[7m` (inverse video)

#### 2. Data Entry Requirements
For interactive input, implement:
- **Cursor Keys**: Send `ESC[A/B/C/D` or `ESC O A/B/C/D`
- **Function Keys**: PF1-PF4 send `ESC O P/Q/R/S`
- **Special Keys**: Must support ESC, TAB, BS, DEL, and LF
- **Terminal Identification**: `ESC[c` requests ID, responds with `ESC[?1;0c` or similar

#### 3. Full-Screen Editing Requirements
For applications like vim in tmux:
- **Selective Erase**: `ESC[0J/1J/2J` (erase down/up/all), `ESC[0K/1K/2K` (erase line)
- **Scrolling Region**: `ESC[12;24r` sets scroll region lines 12-24
- **Application Keypad**: `ESC =` enables, `ESC >` disables application mode

### Character Attributes (SGR - Set Graphics Rendition)

```bash
ESC[0m   # Reset all attributes
ESC[1m   # Bold/bright
ESC[2m   # Dim
ESC[3m   # Italic
ESC[4m   # Underline
ESC[5m   # Slow blink
ESC[6m   # Fast blink
ESC[7m   # Inverse/reverse video
ESC[8m   # Concealed/hidden
ESC[9m   # Crossed out

# Colors (30-37 foreground, 40-47 background)
ESC[30m  # Black text
ESC[31m  # Red text
ESC[32m  # Green text
ESC[33m  # Yellow text
ESC[34m  # Blue text
ESC[35m  # Magenta text
ESC[36m  # Cyan text
ESC[37m  # White text

ESC[40m  # Black background
ESC[41m  # Red background
# ... etc
```

### Terminal Modes

```bash
# Set Mode (SM) - ESC[...h
ESC[4h   # Insert mode
ESC[20h  # Linefeed newline mode (LF → CR+LF)
ESC[?1h  # Cursor keys send ESC O A (application mode)
ESC[?3h  # 132 column mode
ESC[?5h  # Reverse video (black on white)
ESC[?6h  # Origin mode (relative to scroll region)
ESC[?7h  # Auto-wrap at right margin
ESC[?25h # Show cursor

# Reset Mode (RM) - ESC[...l
ESC[4l   # Replace mode
ESC[20l  # Linefeed mode (LF only)
ESC[?1l  # Cursor keys send ESC [ A (normal mode)
ESC[?3l  # 80 column mode
ESC[?5l  # Normal video (white on black)
ESC[?6l  # Absolute origin mode
ESC[?7l  # No auto-wrap
ESC[?25l # Hide cursor
```

### Advanced Control Sequences

```bash
# Cursor Save/Restore
ESC 7    # Save cursor position (DECSC)
ESC 8    # Restore cursor position (DECRC)

# Line Attributes
ESC#3    # Double-height line (top half)
ESC#4    # Double-height line (bottom half)
ESC#5    # Single-width line
ESC#6    # Double-width line

# Scrolling
ESC[S    # Scroll up
ESC[T    # Scroll down
ESC D    # Index (scroll up one line)
ESC M    # Reverse index (scroll down one line)

# Tab Control
ESC H    # Set tab stop at current position
ESC[g    # Clear tab stop at current position
ESC[3g   # Clear all tab stops

# Device Status
ESC[5n   # Request terminal status
ESC[6n   # Request cursor position (CPR)
ESC[0n   # Response: Terminal OK
ESC[3n   # Response: Terminal not OK
ESC[row;colR  # Cursor position report
```

### Tmux-Specific Considerations

1. **256-Color Support**: Use `TERM=screen-256color` or `TERM=tmux-256color`
2. **True Color**: Modern tmux supports 24-bit color with `Tc` capability
3. **Mouse Tracking**: Tmux can pass through mouse events with proper terminal support
4. **Alternate Screen**: Tmux uses alternate screen buffer for full-screen applications

### Debugging Terminal Issues

```bash
# Check terminal capabilities
infocmp $TERM

# Test color support
for i in {0..255}; do
    printf "\x1b[38;5;${i}mcolour${i}\x1b[0m\n"
done

# Verify escape sequences
cat -v  # Shows control characters
od -c   # Shows character codes

# Terminal info in tmux
tmux info
```

## Notes
When assisting with tmux configurations:
- Always consider the user's operating system for clipboard integration
- Be aware of prefix key conflicts with other tools (vim, emacs, etc.)
- Remember that tmux configuration syntax has changed between versions
- Consider suggesting tmuxinator or tmuxp for complex session management
- Mouse support behavior varies between tmux versions
- For pair programming setups, consider tmate as an alternative
- Window/pane indices can start at 0 or 1 based on configuration
- Understanding ANSI escape sequences helps debug display issues
- Terminal compatibility affects features like true color and mouse support