# Ghostty Terminal Emulator Documentation

## Overview

Ghostty is a fast, cross-platform terminal emulator that uses GPU acceleration and platform-native UI. It follows a "zero configuration philosophy" - designed to work perfectly out of the box while offering extensive customization options.

**Key Features:**
- GPU-accelerated rendering
- Platform-native UI integration
- Embedded default font (JetBrains Mono)
- Built-in Nerd Fonts support
- Hundreds of configuration options
- Runtime configuration reloading
- Cross-platform (macOS, Linux)

## Installation

### Via Homebrew (macOS)
```bash
brew install --cask ghostty
```

### Package Installation
Ghostty is typically installed as a GUI application cask rather than a CLI tool.

## Configuration

### Configuration File Locations

Ghostty uses a text-based configuration file with the following priority order:

1. **XDG Path (Linux/macOS)**: `$XDG_CONFIG_HOME/ghostty/config`
2. **Fallback XDG Path**: `$HOME/.config/ghostty/config`
3. **macOS-specific**: `$HOME/Library/Application Support/com.mitchellh.ghostty/config`

If multiple files exist, later files override earlier ones.

### Configuration Syntax

```
# Simple key = value syntax
# Whitespace around equals doesn't matter
# Comments start with #

key = value
another-key = another-value
```

**Important Rules:**
- Keys are case-sensitive
- Empty values reset options to defaults
- Configuration is optional - Ghostty works without any config

### Runtime Configuration Reload

- **Linux**: `Ctrl+Shift+,`
- **macOS**: `Cmd+Shift+,`

## Essential Configuration Options

### Appearance & Theming

```bash
# Theme selection (built-in themes available)
theme = dracula

# Custom colors
background = 282c34
foreground = ffffff
cursor-color = ff0000

# Transparency
background-opacity = 0.9
```

**List Available Themes:**
```bash
ghostty +list-themes
```

### Font Configuration

```bash
# Font family
font-family = JetBrains Mono
font-family = Monaco
font-family = Fira Code

# Font sizing
font-size = 14
font-thicken = true  # Makes thin fonts bolder

# Font features
font-feature = liga=1    # Enable ligatures
font-feature = calt=1    # Enable contextual alternates
```

### Window Management

```bash
# Window dimensions (in character cells)
window-width = 110
window-height = 30

# Window title
title = "Ghostty Terminal"
window-title-font-family = SF Pro Display

# Window behavior
window-save-state = false
window-padding-x = 10
window-padding-y = 10
```

### Advanced Display Options

```bash
# Cursor configuration
cursor-style = block        # block, underline, bar
cursor-style-blink = true

# Minimum contrast ratio (accessibility)
minimum-contrast = 4.5

# Mouse behavior
mouse-hide-while-typing = true
mouse-shift-capture = true

# Alt/Option click cursor positioning
alt-screen-cursor-move = true
```

## Keybindings

### Custom Keybinding Syntax

```bash
# Format: keybind = modifier+key=action
keybind = ctrl+z=close_surface
keybind = ctrl+d=new_split:right
keybind = ctrl+shift+d=new_split:down
keybind = cmd+t=new_tab
keybind = cmd+w=close_surface

# Available modifiers: ctrl, alt, shift, cmd (macOS), super (Linux)
# Actions include: new_tab, close_surface, new_split, etc.
```

### Split Management

```bash
# Split navigation
keybind = ctrl+h=goto_split:left
keybind = ctrl+j=goto_split:down
keybind = ctrl+k=goto_split:up
keybind = ctrl+l=goto_split:right

# Split creation
keybind = ctrl+shift+backslash=new_split:right
keybind = ctrl+shift+minus=new_split:down
```

## Security & Privacy

### Clipboard Security

```bash
# Clipboard paste protection
clipboard-paste-bracketed-safe = true
clipboard-paste-protection = true

# Confirm dangerous pastes
clipboard-paste-confirm = true
```

### Title Reporting

```bash
# Disable title reporting for security
allow-title-reporting = false
```

### OSC (Operating System Command) Controls

```bash
# Control which OSC sequences are allowed
osc-color-report-format = none
```

## Advanced Features

### Image Protocol Support

```bash
# Kitty image protocol configuration
image-storage-limit = 320MB    # Maximum image data storage
```

### Shell Integration

```bash
# Enable shell integration features
shell-integration = true
shell-integration-features = cursor,sudo,title
```

### GPU Acceleration

```bash
# GPU renderer configuration (usually auto-detected)
renderer = auto    # Options: auto, opengl, software
```

## Command Line Usage

### Configuration Commands

```bash
# Show current configuration with documentation
ghostty +show-config --default --docs

# List all available themes
ghostty +list-themes

# Launch with specific config
ghostty --config-file=/path/to/config

# Launch with inline config
ghostty --font-size=16 --theme=dracula
```

### Debug & Information

```bash
# Show version information
ghostty --version

# Show build information
ghostty +show-build-info

# Debug configuration loading
ghostty +show-config --debug
```

## Best Practices

### 1. Minimal Configuration Approach

Start with Ghostty's defaults and only configure what you need:

```bash
# Minimal useful config
theme = tokyo-night
font-size = 14
window-padding-x = 8
window-padding-y = 8
```

### 2. Theme-Based Configuration

Use built-in themes as a base, then customize:

```bash
theme = gruvbox-dark
# Override specific colors if needed
cursor-color = #fe8019
```

### 3. Platform-Specific Configurations

#### macOS-Specific Settings
```bash
# Option key behavior
macos-option-as-alt = true

# Titlebar styling
macos-titlebar-style = tabs    # Options: auto, tabs, hidden

# Global keybindings (requires accessibility permissions)
keybind = global:cmd+grave=toggle_quick_terminal
```

#### Linux-Specific Settings
```bash
# Process isolation
linux-cgroup = always    # Options: auto, always, never

# GTK application behavior
gtk-single-instance = true

# Desktop integration
gtk-adwaita = true
```

### 4. Performance Optimization

```bash
# For better performance
frame-rate = 60
sync-to-monitor = true
```

### 5. Accessibility Configuration

```bash
# High contrast for accessibility
minimum-contrast = 7.0
cursor-style-blink = false
font-size = 16
```

## Common Configuration Examples

### Developer Setup

```bash
theme = tokyo-night
font-family = JetBrains Mono
font-size = 14
font-feature = liga=1
window-width = 120
window-height = 40
keybind = cmd+d=new_split:right
keybind = cmd+shift+d=new_split:down
shell-integration = true
```

### Minimal Setup

```bash
font-size = 16
theme = dracula
window-padding-x = 10
window-padding-y = 10
```

### High Performance Setup

```bash
renderer = opengl
frame-rate = 120
sync-to-monitor = true
font-thicken = false
background-opacity = 1.0
```


## Integration Tips

### Shell Integration

Enable shell integration for enhanced features:

```bash
# In ghostty config
shell-integration = true
shell-integration-features = cursor,sudo,title,jump

# Shell integration auto-injection enables:
# - Working directory reporting for new tabs/splits
# - Prompt marking for jump_to_prompt keybinding  
# - Smart terminal closing (no confirmation at prompt)
# - Better window resizing with complex prompts

# In shell profile (.zshrc, .bashrc)
eval "$(ghostty +shell-integration)"
```

### Terminal Multiplexer Integration

Ghostty works well with tmux, screen, and other multiplexers:

```bash
# Disable ghostty's built-in tabs if using tmux
keybind = cmd+t=no-op
```

### Editor Integration

Configure for better editor experience:

```bash
# Better cursor for vim/nvim
cursor-style = block
cursor-style-blink = false

# Alt key support for editors
alt-screen-cursor-move = true
```

## Version History & Release Notes

### Ghostty 1.0 (December 2024)
- First public release under MIT license
- Cross-platform support (macOS, Linux)
- GPU-accelerated rendering (Metal on macOS, OpenGL on Linux)
- Platform-native UI (SwiftUI on macOS, GTK4 on Linux)
- Hundreds of built-in themes
- Extensive configuration options
- Shell integration features
- Quick terminal functionality
- Global keybindings support (macOS)

### Development History
- 2+ years of development by Mitchell Hashimoto
- ~2,000 beta testers across platforms
- Focus on performance and native platform integration
- Windows support planned for post-1.0

## Performance Characteristics

### Rendering Performance
- Multi-renderer architecture
- Metal renderer on macOS (only terminal with Metal + ligatures)
- OpenGL renderer on Linux
- Software fallback renderer
- GPU acceleration for smooth rendering
- Competitive with highest-performing terminal emulators

### Standards Compliance
- More xterm escape sequences than any other terminal (except xterm)
- Support for modern terminal specifications
- Kitty image protocol support
- Extensive color palette support (256-color + true color)

## Troubleshooting

### Performance Issues

1. **Slow rendering**: Try different renderer
   ```bash
   renderer = software  # or opengl, metal
   ```

2. **High CPU usage**: Reduce frame rate
   ```bash
   frame-rate = 30
   ```

3. **Memory issues**: Limit image storage
   ```bash
   image-storage-limit = 160MB
   ```

### Configuration Issues

1. **Config not loading**: Check file path and permissions
   ```bash
   ghostty +show-config --debug
   ```

2. **Font not found**: Verify font installation
   ```bash
   ghostty +list-fonts | grep -i "font-name"
   ```

3. **Theme not applying**: Ensure theme name is correct
   ```bash
   ghostty +list-themes | grep theme-name
   ```

4. **Keybindings not working**: Validate configuration
   ```bash
   ghostty +validate-config
   ghostty +list-keybinds
   ```

### Platform-Specific Issues

#### macOS
- **Option key issues**: Set `macos-option-as-alt = true`
- **Titlebar problems**: Adjust `macos-titlebar-style`
- **Global keybindings**: Requires accessibility permissions
- **Quick terminal**: Enable with global keybinding

#### Linux
- **Font rendering**: Check fontconfig settings
- **GPU acceleration**: Verify graphics drivers
- **GTK theming**: Use `gtk-adwaita = true`
- **Single instance**: Configure `gtk-single-instance`

## Reference Links

- **Official Website**: https://ghostty.org/
- **Official Documentation**: https://ghostty.org/docs
- **Configuration Reference**: https://ghostty.org/docs/config/reference
- **Keybinding Reference**: https://ghostty.org/docs/config/keybind/reference
- **GitHub Repository**: https://github.com/ghostty-org/ghostty
- **Built-in Help**: `ghostty +help`
- **Configuration Help**: `ghostty +show-config --docs`
- **Author's Blog**: Mitchell Hashimoto's writings on Ghostty development

---

*This comprehensive documentation covers all essential aspects of Ghostty terminal emulator configuration, features, and usage for AI agents and users working with this modern, high-performance terminal emulator.*