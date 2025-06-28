# Configuration Reference

This document provides a comprehensive reference for configuring the dotfiles TUI manager.

## Table of Contents

1. [Configuration File Location](#configuration-file-location)
2. [Global Configuration](#global-configuration)
3. [TUI Configuration](#tui-configuration)
4. [Package Configuration](#package-configuration)
5. [Tool Configuration](#tool-configuration)
6. [Theme Configuration](#theme-configuration)
7. [Performance Configuration](#performance-configuration)
8. [Environment Variables](#environment-variables)
9. [Validation and Schemas](#validation-and-schemas)
10. [Examples](#examples)

## Configuration File Location

The configuration file is located at:
- **Primary**: `~/.config/dotfiles/config.yaml`
- **Fallback**: `~/.dotfiles/config.yaml`

The system will automatically create a default configuration file if none exists.

## Global Configuration

The `global` section contains system-wide settings:

```yaml
global:
  # Path to your dotfiles directory
  dotfiles_path: "/Users/username/.dotfiles"
  
  # Logging configuration
  log_level: "info"  # debug, info, warn, error
  log_file: ""       # Empty for stderr, or path to log file
  
  # Operational settings
  dry_run: false           # Preview changes without applying
  auto_confirm: false      # Skip confirmation prompts
  backup_enabled: true     # Create backups before changes
  backup_suffix: ".backup" # Suffix for backup files
  backup_dir: ""           # Custom backup directory (empty for auto)
  
  # Concurrency settings
  max_concurrent: 5        # Maximum concurrent operations
  timeout: "30s"           # Default timeout for operations
```

### Global Configuration Options

#### `dotfiles_path` (string, required)
- **Description**: Absolute path to your dotfiles directory
- **Default**: `~/.dotfiles`
- **Example**: `/home/user/my-dotfiles`

#### `log_level` (string)
- **Description**: Minimum log level to display
- **Options**: `debug`, `info`, `warn`, `error`
- **Default**: `info`

#### `dry_run` (boolean)
- **Description**: Preview changes without applying them
- **Default**: `false`
- **Note**: Can be overridden with `--dry-run` flag

#### `auto_confirm` (boolean)
- **Description**: Skip interactive confirmation prompts
- **Default**: `false`
- **Warning**: Use with caution in automation

#### `backup_enabled` (boolean)
- **Description**: Create backups before modifying files
- **Default**: `true`
- **Recommendation**: Keep enabled for safety

## TUI Configuration

The `tui` section configures the terminal user interface:

```yaml
tui:
  # Appearance
  color_scheme: "default"     # Theme name to use
  animations: true            # Enable UI animations
  unicode_support: true       # Use Unicode characters
  
  # Behavior
  confirm_destructive: true   # Confirm dangerous operations
  show_progress: true         # Show progress bars
  auto_refresh: true          # Auto-refresh status
  refresh_interval: "5s"      # How often to refresh
  
  # Layout
  split_ratio: 0.3           # Sidebar width ratio
  min_width: 80              # Minimum terminal width
  min_height: 24             # Minimum terminal height
  
  # Keyboard shortcuts
  vim_mode: false            # Enable vim-style navigation
  shortcuts:
    quit: ["q", "ctrl+c"]
    help: ["?", "F1"]
    refresh: ["F5", "ctrl+r"]
```

### TUI Configuration Options

#### `color_scheme` (string)
- **Description**: Name of the theme to use
- **Default**: `default`
- **Options**: `default`, `light`, `dark`, `cyberpunk`, or custom theme name

#### `animations` (boolean)
- **Description**: Enable smooth transitions and animations
- **Default**: `true`
- **Note**: Disable for better performance on slow terminals

#### `confirm_destructive` (boolean)
- **Description**: Show confirmation for destructive operations
- **Default**: `true`
- **Examples**: Package removal, file deletion

#### `vim_mode` (boolean)
- **Description**: Enable vim-style keyboard navigation
- **Default**: `false`
- **Keys**: `h/j/k/l` for navigation, `/` for search

## Package Configuration

The `stow` section configures package management using GNU Stow:

```yaml
stow:
  # Default settings for all packages
  target: "/Users/username"   # Default target directory
  verbose: false              # Verbose stow operations
  simulate: false             # Simulation mode
  
  # Package definitions
  packages:
    - name: "vim"             # Package directory name
      target: "/Users/username" # Override default target
      enabled: true           # Enable this package
      priority: 1            # Installation priority (lower first)
      
      # File filtering
      include:                # Only include these patterns
        - ".vimrc"
        - ".vim/"
      exclude:                # Exclude these patterns
        - ".vim/temp/"
        - "*.swp"
        - "*.backup"
      
      # Dependencies
      depends_on:             # Packages this depends on
        - "git"
      conflicts_with:         # Incompatible packages
        - "nvim"
      
      # Hooks
      before_install:         # Commands to run before install
        - "echo 'Installing vim config'"
      after_install:          # Commands to run after install
        - "vim +PlugInstall +qall"
      before_remove:          # Commands to run before removal
        - "echo 'Removing vim config'"
```

### Package Configuration Options

#### Package Definition

Each package in the `packages` array supports:

#### `name` (string, required)
- **Description**: Directory name in dotfiles folder
- **Must match**: Actual directory name in `dotfiles_path`

#### `enabled` (boolean)
- **Description**: Whether to install this package
- **Default**: `true`

#### `priority` (integer)
- **Description**: Installation order (lower numbers first)
- **Default**: `100`
- **Range**: `1-1000`

#### `target` (string)
- **Description**: Where to install package files
- **Default**: Global `target` setting
- **Usually**: User's home directory

#### `include` (array of strings)
- **Description**: Glob patterns for files to include
- **Default**: Include all files
- **Example**: `["*.conf", "bin/"]`

#### `exclude` (array of strings)
- **Description**: Glob patterns for files to exclude
- **Default**: Empty (exclude nothing)
- **Example**: `["*.log", "temp/", "*.backup"]`

#### `depends_on` (array of strings)
- **Description**: Package dependencies
- **Behavior**: Dependencies installed first
- **Example**: `["git", "zsh"]`

#### `conflicts_with` (array of strings)
- **Description**: Conflicting packages
- **Behavior**: Cannot be enabled simultaneously
- **Example**: `["vim", "nvim"]`

## Tool Configuration

The `tools` section configures integration with external tools:

```yaml
tools:
  # Homebrew (macOS package manager)
  homebrew:
    enabled: true             # Enable Homebrew integration
    auto_update: false        # Auto-update before operations
    cask_enabled: true        # Support Homebrew Cask
    tap_enabled: true         # Support custom taps
    cleanup_enabled: true     # Auto-cleanup old versions
    
    # Custom configuration
    brew_command: "brew"      # Command to use
    install_missing: true     # Install Homebrew if missing
    
  # NPM (Node.js package manager)
  npm:
    enabled: true             # Enable NPM integration
    global_packages: true     # Manage global packages
    registry: "https://registry.npmjs.org/"
    
    # Version management
    node_version: ""          # Specific Node.js version
    npm_version: ""           # Specific NPM version
    
  # APT (Debian/Ubuntu package manager)
  apt:
    enabled: false            # Enable on Debian/Ubuntu
    auto_update: false        # Auto-update package lists
    auto_upgrade: false       # Auto-upgrade packages
    install_recommends: true  # Install recommended packages
    
  # Pip (Python package manager)
  pip:
    enabled: true             # Enable Pip integration
    user_packages: true       # Install to user directory
    python_version: "3"       # Python version (2 or 3)
    virtual_env: ""           # Virtual environment path
    
  # Cargo (Rust package manager)
  cargo:
    enabled: false            # Enable Cargo integration
    install_locked: true      # Use locked versions
    target_dir: ""            # Custom target directory
```

### Tool-Specific Options

#### Homebrew Options

- `auto_update`: Update Homebrew before package operations
- `cask_enabled`: Support GUI applications via Homebrew Cask
- `cleanup_enabled`: Remove old package versions automatically

#### NPM Options

- `global_packages`: Manage global NPM packages
- `registry`: Custom NPM registry URL
- `node_version`: Pin to specific Node.js version

#### APT Options

- `auto_update`: Run `apt update` before operations
- `install_recommends`: Install recommended packages

#### Pip Options

- `user_packages`: Install to user directory (`--user` flag)
- `python_version`: Target Python version

## Theme Configuration

The `themes` section defines custom color schemes:

```yaml
themes:
  # Custom theme definition
  my-theme:
    # Core colors
    primary: "#007acc"        # Primary accent color
    secondary: "#4ec9b0"      # Secondary accent color
    success: "#4ec9b0"        # Success state color
    warning: "#ffcc02"        # Warning state color
    error: "#f14c4c"          # Error state color
    background: "#1e1e1e"     # Background color
    foreground: "#d4d4d4"     # Default text color
    
    # UI element colors
    border: "#464647"         # Border color
    highlight: "#094771"      # Highlight color
    selection: "#264f78"      # Selection color
    
    # Text colors
    text_primary: "#d4d4d4"   # Primary text
    text_secondary: "#969696" # Secondary text
    text_muted: "#6a6a6a"     # Muted text
    
    # Status colors
    status_enabled: "#4ec9b0"   # Enabled items
    status_disabled: "#969696"  # Disabled items
    status_error: "#f14c4c"     # Error items
    status_warning: "#ffcc02"   # Warning items
    
  # Inherit from existing theme
  my-variant:
    inherit_from: "default"   # Base theme
    primary: "#ff6b35"        # Override specific colors
    error: "#ff1744"
```

### Theme Configuration Options

#### Core Colors

Required colors for theme functionality:

- `primary`: Main accent color for interactive elements
- `secondary`: Secondary accent for supporting elements
- `success`: Color for successful operations and positive states
- `warning`: Color for warnings and caution states
- `error`: Color for errors and critical states
- `background`: Main background color
- `foreground`: Default text color

#### Advanced Colors

Optional colors for fine-tuned styling:

- `border`: Border and separator colors
- `highlight`: Hover and focus states
- `selection`: Selected item background
- `text_*`: Various text hierarchy levels
- `status_*`: Status indicator colors

#### Theme Inheritance

Use `inherit_from` to base a theme on an existing one:

```yaml
themes:
  my-dark-theme:
    inherit_from: "dark"
    primary: "#00d4aa"      # Just change the accent color
```

## Performance Configuration

The `performance` section configures optimization features:

```yaml
performance:
  # Monitoring
  monitoring_enabled: false   # Enable performance monitoring
  monitoring_interval: "5s"   # Monitoring collection interval
  
  # Caching
  cache_enabled: true         # Enable operation caching
  cache_size: 1000           # Maximum cache entries
  cache_ttl: "5m"            # Cache time-to-live
  
  # Memory management
  gc_percent: 100            # GC target percentage
  max_memory: "512MB"        # Maximum memory usage
  
  # Concurrency
  max_workers: 10            # Maximum worker goroutines
  worker_timeout: "30s"      # Worker operation timeout
  
  # Profiling (development only)
  profiling_enabled: false   # Enable pprof profiling
  profile_dir: "./profiles"  # Profile output directory
  cpu_profile: false         # Enable CPU profiling
  memory_profile: false      # Enable memory profiling
```

### Performance Options

#### Monitoring Options

- `monitoring_enabled`: Collect performance metrics
- `monitoring_interval`: How often to collect metrics

#### Caching Options

- `cache_enabled`: Enable result caching for expensive operations
- `cache_size`: Maximum number of cached items
- `cache_ttl`: How long to keep cached items

#### Memory Options

- `gc_percent`: Go garbage collector target
- `max_memory`: Maximum memory usage limit

## Environment Variables

Override configuration with environment variables:

### Global Settings
```bash
export DOTFILES_PATH="/custom/dotfiles"
export DOTFILES_LOG_LEVEL="debug"
export DOTFILES_DRY_RUN="true"
export DOTFILES_AUTO_CONFIRM="false"
```

### TUI Settings
```bash
export DOTFILES_THEME="cyberpunk"
export DOTFILES_ANIMATIONS="false"
export DOTFILES_VIM_MODE="true"
```

### Tool Settings
```bash
export DOTFILES_HOMEBREW_ENABLED="true"
export DOTFILES_NPM_ENABLED="false"
export DOTFILES_APT_AUTO_UPDATE="true"
```

### Performance Settings
```bash
export DOTFILES_CACHE_ENABLED="true"
export DOTFILES_MONITORING_ENABLED="true"
export DOTFILES_MAX_WORKERS="5"
```

## Validation and Schemas

### Configuration Validation

The system validates configuration on startup:

```bash
# Validate current configuration
dotfiles config validate

# Validate specific file
dotfiles config validate --file custom-config.yaml

# Show validation errors in detail
dotfiles config validate --verbose
```

### Schema Reference

The configuration follows a strict schema. Key validation rules:

- `dotfiles_path` must be an absolute path to an existing directory
- `log_level` must be one of: debug, info, warn, error
- Package names must match actual directory names
- Tool names must be supported tool types
- Colors must be valid hex codes (#RRGGBB format)
- Durations must be valid Go duration strings (1s, 5m, 2h)

### Error Handling

Common validation errors and solutions:

#### Invalid Path Error
```yaml
# Error: dotfiles_path is not absolute
dotfiles_path: "~/dotfiles"

# Solution: Use absolute path
dotfiles_path: "/Users/username/dotfiles"
```

#### Invalid Color Error
```yaml
# Error: Invalid color format
themes:
  my-theme:
    primary: "blue"  # Invalid

# Solution: Use hex format
themes:
  my-theme:
    primary: "#0000ff"  # Valid
```

#### Package Not Found Error
```yaml
# Error: Package directory doesn't exist
packages:
  - name: "nonexistent"

# Solution: Create directory or fix name
packages:
  - name: "vim"  # Must exist in dotfiles_path/vim/
```

## Examples

### Complete Configuration Example

```yaml
# ~/.config/dotfiles/config.yaml
global:
  dotfiles_path: "/Users/john/.dotfiles"
  log_level: "info"
  backup_enabled: true
  backup_suffix: ".backup"
  auto_confirm: false

tui:
  color_scheme: "cyberpunk"
  animations: true
  confirm_destructive: true
  show_progress: true
  vim_mode: false

stow:
  target: "/Users/john"
  packages:
    - name: "git"
      enabled: true
      priority: 1
    - name: "vim"
      enabled: true
      priority: 2
      depends_on: ["git"]
      exclude: ["*.swp", "temp/"]
    - name: "zsh"
      enabled: true
      priority: 3
      after_install:
        - "source ~/.zshrc"

tools:
  homebrew:
    enabled: true
    auto_update: false
    cask_enabled: true
  npm:
    enabled: true
    global_packages: true
  pip:
    enabled: true
    user_packages: true

themes:
  cyberpunk:
    primary: "#00d4aa"
    secondary: "#ff6b35"
    success: "#00d4aa"
    warning: "#ffcc02"
    error: "#ff1744"
    background: "#0a0a0a"
    foreground: "#00ff00"

performance:
  cache_enabled: true
  cache_size: 2000
  monitoring_enabled: false
```

### Minimal Configuration Example

```yaml
# Minimal working configuration
global:
  dotfiles_path: "/Users/jane/.dotfiles"

stow:
  packages:
    - name: "vim"
      enabled: true
    - name: "git"
      enabled: true
```

### Development Configuration Example

```yaml
# Development setup with debugging
global:
  dotfiles_path: "/Users/dev/dotfiles"
  log_level: "debug"
  dry_run: true

tui:
  animations: false  # Faster for testing
  
performance:
  monitoring_enabled: true
  profiling_enabled: true
  profile_dir: "./dev-profiles"
  
tools:
  homebrew:
    enabled: true
  npm:
    enabled: true
```

This configuration reference provides comprehensive documentation for all available options and settings in the dotfiles TUI manager.