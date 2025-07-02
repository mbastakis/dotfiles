# User Guide

Welcome to the dotfiles TUI manager! This guide will help you get started and make the most of the interactive terminal interface for managing your dotfiles.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [TUI Interface](#tui-interface)
4. [Package Management](#package-management)
5. [Tool Integration](#tool-integration)
6. [Theme System](#theme-system)
7. [Configuration](#configuration)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

1. **Download and Install**
   ```bash
   # Clone the repository
   git clone <repository-url> ~/.dotfiles
   cd ~/.dotfiles
   
   # Build the application
   go build -o dotfiles cmd/dotfiles/main.go
   
   # Make it available globally
   sudo mv dotfiles /usr/local/bin/
   ```

2. **Initial Setup**
   ```bash
   # Initialize configuration
   dotfiles init
   
   # Start the TUI
   dotfiles tui
   ```

### First Launch

When you first launch the TUI, you'll see:

- **Welcome Screen**: Overview of your dotfiles setup
- **Quick Setup Wizard**: Guided configuration
- **Main Menu**: Navigation to different sections

Follow the setup wizard to configure:
- Dotfiles directory location
- Default package manager preferences
- Theme selection

## Basic Usage

### Command Line Interface

```bash
# Start the interactive TUI
dotfiles tui

# Quick commands without TUI
dotfiles sync              # Sync all packages
dotfiles packages list     # List packages
dotfiles themes list       # List available themes
dotfiles tools status      # Check tool status

# Help and information
dotfiles help              # Show help
dotfiles version           # Show version
dotfiles config show       # Show current configuration
```

### Common Workflows

**Daily Usage:**
```bash
# Quick sync of dotfiles
dotfiles sync

# Check status
dotfiles status

# Update tools
dotfiles tools update
```

**Package Management:**
```bash
# Add a new package
dotfiles packages add vim

# Enable/disable packages
dotfiles packages enable vim
dotfiles packages disable old-config

# List package status
dotfiles packages status
```

## TUI Interface

### Navigation

The TUI uses intuitive keyboard controls:

- **Arrow Keys / hjkl**: Navigate menus and options
- **Enter**: Select item or execute action
- **Space**: Toggle selections (checkboxes)
- **Tab**: Switch between panels
- **Esc**: Go back or cancel
- **q**: Quit application
- **?**: Show help for current screen

### Main Screens

#### 1. Overview Screen
- System status at a glance
- Quick actions and shortcuts
- Recent activity and notifications
- Performance metrics (if enabled)

#### 2. Packages Screen
- List of all packages with status
- Enable/disable packages
- Package details and dependencies
- Installation and removal actions

#### 3. Tools Screen
- Integrated tool management
- Tool status and health checks
- Installation and configuration
- Bulk operations

#### 4. Themes Screen
- Theme selection and preview
- Color scheme customization
- Import/export themes
- Live preview of changes

#### 5. Settings Screen
- Configuration management
- Performance settings
- Advanced options

### Interactive Elements

**Lists and Tables:**
- Sortable columns (click headers)
- Filter and search functionality
- Multi-selection with space
- Context menus with right-click

**Forms and Dialogs:**
- Tab navigation between fields
- Validation with error messages
- Auto-completion where applicable
- Help text and examples

**Progress Indicators:**
- Real-time progress bars
- Status updates during operations
- Cancellation support
- Error handling and recovery

## Package Management

### Package Structure

Packages are organized using GNU Stow conventions:

```
~/.dotfiles/
├── vim/              # Package directory
│   ├── .vimrc       # Configuration file
│   └── .vim/        # Configuration directory
├── zsh/
│   ├── .zshrc
│   └── .zsh/
└── git/
    └── .gitconfig
```

### Package Operations

#### Adding Packages

1. **Through TUI:**
   - Navigate to Packages screen
   - Click "Add Package" button
   - Fill in package details
   - Select files to include

2. **Manual Creation:**
   ```bash
   # Create package directory
   mkdir ~/.dotfiles/mypackage
   
   # Add configuration files
   cp ~/.myconfig ~/.dotfiles/mypackage/
   
   # Enable in TUI or command line
   dotfiles packages enable mypackage
   ```

#### Package Configuration

Each package can have specific settings:

```yaml
# In config.yaml
stow:
  packages:
    - name: "vim"
      target: "/Users/username"
      enabled: true
      priority: 1
      include:
        - ".vimrc"
        - ".vim/"
      exclude:
        - ".vim/temp/"
        - ".vim/*.swp"
```

#### Bulk Operations

Use the TUI for efficient bulk operations:
- Select multiple packages with Space
- Apply actions to selection
- Progress tracking for long operations
- Rollback capability for errors

### Package Dependencies

Define dependencies between packages:

```yaml
packages:
  - name: "dev-environment"
    depends_on:
      - "vim"
      - "git"
      - "zsh"
    enabled: true
```

## Tool Integration

### Supported Tools

The system integrates with popular package managers and tools:

- **Homebrew** (macOS package manager)
- **APT** (Debian/Ubuntu package manager)
- **NPM** (Node.js package manager)
- **Pip** (Python package manager)
- **Cargo** (Rust package manager)

### Tool Configuration

Configure tools in the TUI Settings screen or config file:

```yaml
tools:
  homebrew:
    enabled: true
    auto_update: false
    cask_enabled: true
  npm:
    enabled: true
    global_packages: true
    registry: "https://registry.npmjs.org/"
```

### Tool Operations

#### Status Checking
- Real-time health monitoring
- Dependency verification
- Version checking
- Error detection and reporting

#### Installation Management
- Install missing tools
- Update to latest versions
- Remove unused packages

#### Bulk Operations
- Update all tools at once
- Install from package lists
- Sync across multiple machines
- Generate installation scripts

## Theme System

### Built-in Themes

The system includes several built-in themes:

- **Default**: Balanced colors for general use
- **Light**: Light background with dark text
- **Dark**: Dark background with light text
- **Cyberpunk**: High-contrast neon colors
- **Minimalist**: Subtle colors with minimal styling

### Theme Selection

1. **Through TUI:**
   - Navigate to Themes screen
   - Preview themes in real-time
   - Click to apply immediately

2. **Command Line:**
   ```bash
   dotfiles themes set cyberpunk
   dotfiles themes current
   ```

### Custom Themes

Create custom themes by defining color schemes:

```yaml
themes:
  my-theme:
    primary: "#007acc"      # Primary accent color
    secondary: "#4ec9b0"    # Secondary accent color
    success: "#4ec9b0"      # Success states
    warning: "#ffcc02"      # Warning states
    error: "#f14c4c"        # Error states
    background: "#1e1e1e"   # Background color
    foreground: "#d4d4d4"   # Text color
```

### Theme Features

- **Live Preview**: See changes immediately
- **Component Theming**: Different colors for different UI elements
- **Export/Import**: Share themes with others
- **Inheritance**: Base themes on existing ones

## Configuration

### Configuration File

The main configuration file is located at `~/.config/dotfiles/config.yaml`:

```yaml
global:
  dotfiles_path: "/Users/username/.dotfiles"
  log_level: "info"
  dry_run: false
  auto_confirm: false

tui:
  color_scheme: "default"
  animations: true
  confirm_destructive: true
  show_progress: true

stow:
  packages:
    - name: "vim"
      enabled: true
      priority: 1

tools:
  homebrew:
    enabled: true
```

### Configuration Management

#### Through TUI
- Settings screen provides forms for all options
- Real-time validation and error checking
- Help text and examples for each setting
- Save/load configuration profiles

#### Command Line
```bash
# View current configuration
dotfiles config show

# Validate configuration
dotfiles config validate

# Edit specific values
dotfiles config set global.log_level debug
dotfiles config set tui.animations false
```

### Environment Variables

Override configuration with environment variables:

```bash
export DOTFILES_LOG_LEVEL=debug
export DOTFILES_DRY_RUN=true
export DOTFILES_THEME=cyberpunk
```

## Advanced Features

### Performance Monitoring

Enable performance monitoring for insights:

```yaml
performance:
  monitoring_enabled: true
  cache_enabled: true
  profiling_enabled: false
```

View performance metrics in the TUI Overview screen:
- Memory usage
- Operation timing
- Cache hit ratios
- System resource usage

### File Safety

- Destructive operations require confirmation
- Dry-run mode available for testing changes
- GNU Stow provides built-in backup functionality for symlink operations

### Scripting and Automation

#### Custom Commands
Define custom workflows in configuration:

```yaml
custom_commands:
  setup-dev:
    description: "Set up development environment"
    commands:
      - "dotfiles packages enable vim git zsh"
      - "dotfiles tools npm install"
      - "dotfiles sync"

  daily-update:
    description: "Daily maintenance"
    commands:
      - "dotfiles tools update --quiet"
      - "dotfiles sync"
```

#### Hooks
Set up hooks for automatic actions:

```yaml
hooks:
  before_sync:
    - "echo 'Starting sync...'"
  after_sync:
    - "echo 'Sync completed'"
    - "notify-send 'Dotfiles synced'"
```

### Multi-Machine Sync

Synchronize configuration across multiple machines:

1. **Export Configuration**
   ```bash
   dotfiles export --profile work-laptop
   ```

2. **Import on Another Machine**
   ```bash
   dotfiles import work-laptop.yaml
   ```

3. **Selective Sync**
   ```yaml
   profiles:
     work-laptop:
       packages: ["vim", "git", "work-tools"]
       tools: ["homebrew", "npm"]
     personal:
       packages: ["vim", "git", "games"]
       tools: ["homebrew"]
   ```

## Troubleshooting

### Common Issues

#### Issue: TUI Not Starting
```bash
# Check dependencies
dotfiles doctor

# Verify terminal compatibility
echo $TERM

# Run with debug logging
dotfiles --log-level debug tui
```

#### Issue: Packages Not Syncing
```bash
# Check package status
dotfiles packages status

# Verify file permissions
ls -la ~/.dotfiles/

# Run in dry-run mode
dotfiles --dry-run sync
```

#### Issue: Tool Integration Failing
```bash
# Check tool installation
dotfiles tools doctor

# Verify tool paths
which brew npm pip

# Test individual tools
dotfiles tools homebrew status
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Command line debug
dotfiles --log-level debug --verbose <command>

# TUI debug mode
DOTFILES_LOG_LEVEL=debug dotfiles tui
```

### Log Files

Check log files for error details:

```bash
# View recent logs
dotfiles logs tail

# Search logs
dotfiles logs search "error"

# Export logs for support
dotfiles logs export > support-logs.txt
```

### Getting Help

1. **Built-in Help**
   - Press `?` in any TUI screen
   - Use `dotfiles help <command>`

2. **Documentation**
   - [Configuration Reference](./CONFIGURATION.md)
   - [Migration Guide](./MIGRATION.md)
   - [Performance Guide](./PERFORMANCE.md)

3. **Community Support**
   - GitHub Issues for bugs
   - Discussions for questions
   - Wiki for community guides

### Reset and Recovery

If you need to reset the system:

```bash
# Reset configuration to defaults
dotfiles reset config

# Clear all symlinks
dotfiles clean --all

# Reinitialize
dotfiles init
```

This user guide covers the essential features and workflows for using the dotfiles TUI manager effectively. The interactive interface makes managing your dotfiles intuitive and efficient, while the powerful underlying system handles the complexity of package management and synchronization.