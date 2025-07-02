# Dotfiles TUI CLI Tool Refactor Specification

## High Level Objective

Transform the current bash script-based dotfiles management system into a modern, maintainable Go CLI application with an interactive TUI interface using the bubbletea framework. The new tool will be completely dynamic and configuration-driven, supporting 6 core utilities: **stow**, **rsync**, **homebrew**, **apps**, **npm**, and **uv**. Every aspect will be configurable without hardcoded application-specific logic.

### Core Goals
- **Unified Interface**: Single binary providing both CLI and TUI modes
- **Dynamic Architecture**: Tool behavior entirely driven by YAML configuration
- **Tool Agnostic**: Support for stow, rsync, homebrew, custom apps, npm, and uv packages
- **Maintainability**: Replace complex bash scripts with structured Go code
- **Configurability**: Comprehensive configuration system with bidirectional persistence
- **Testability**: Full test coverage with dry-run capabilities
- **User Experience**: Intuitive TUI interface with keyboard shortcuts and visual feedback
- **Extensibility**: Easy to add new tools without code changes

## Changes for the Refactor

### 1. Repository Structure

```
dotfiles/
├── cmd/
│   └── dotfiles/           # Main CLI entry point
├── internal/
│   ├── config/            # Configuration management and validation
│   ├── tools/             # Dynamic tool integrations
│   │   ├── stow/          # GNU Stow integration
│   │   ├── rsync/         # Rsync integration
│   │   ├── homebrew/      # Homebrew package management
│   │   ├── npm/           # NPM global package management
│   │   ├── uv/            # UV tool package management
│   │   ├── apps/          # Custom application scripts
│   │   └── interface.go   # Tool interface definition
│   ├── tui/               # Bubbletea TUI components
│   │   ├── models/        # TUI models and state
│   │   ├── components/    # Reusable UI components
│   │   └── screens/       # Screen/page implementations
│   ├── cli/               # CLI command implementations
│   ├── engine/            # Dynamic execution engine
│   ├── utils/             # Shared utilities
│   └── types/             # Common types and interfaces
├── pkg/
│   └── dotfiles/          # Public API (if needed)
├── config/                # Dotfiles configurations (stow packages)
│   ├── config/            # Maps to ~/.config (stow package)
│   ├── shell/             # Shell configurations (stow package)
│   │   ├── .zshrc         # Shell config files
│   │   └── .zshprofile    # More shell files
│   ├── git/               # Git configurations (stow package)
│   ├── vscode/            # VS Code settings (stow package)
│   ├── obsidian/          # Obsidian configurations (stow package)
│   └── ...                # Other stow packages
├── data/                  # Non-config data files
│   ├── ai_docs/           # AI documentation
│   ├── specs/             # Project specifications
│   └── scripts/           # Utility scripts
├── homebrew/              # Homebrew package definitions
│   ├── Brewfile
│   ├── Brewfile.apps
│   ├── Brewfile.dev
│   └── Brewfile.mas
├── templates/             # Default configuration templates
├── test/
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test data
├── docs/                  # Documentation
├── go.mod
├── go.sum
├── Makefile
└── README.md
```

### 2. Configuration System

#### ~/.config/dotfiles/config.yaml
```yaml
# Global settings
global:
  dotfiles_path: "~/dev/dotfiles"
  log_level: "info"
  dry_run: false
  auto_confirm: false
  backup_enabled: true
  backup_suffix: ".backup"

# TUI preferences
tui:
  color_scheme: "default"
  animations: true
  confirm_destructive: true
  show_progress: true

# Stow configuration
stow:
  packages:
    - name: "config"
      target: "~/.config"
      enabled: true
      priority: 1
    - name: "shell"
      target: "~/"
      enabled: true
      priority: 2
    - name: "git"
      target: "~/"
      enabled: true
      priority: 3
    - name: "docker"
      target: "~/"
      enabled: false
      priority: 4
    - name: "warp"
      target: "~/"
      enabled: true
      priority: 5
    - name: "vscode"
      target: "~/$VSCODE_USER_DIR/"
      enabled: true
      priority: 6
    - name: "obsidian"
      target: "~/$OBSIDIAN_VAULT_DIR/"
      enabled: true
      priority: 7
    - name: "ai_docs"
      target: "~/dev/ai_docs"
      enabled: true
      priority: 8
    - name: "specs"
      target: "~/dev/specs"
      enabled: true
      priority: 9

# RSync configuration
rsync:
  enabled: true
  sources:
    - name: "claude"
      target: "~/"
      enabled: true
      priority: 1
    - name: "vscode_extensions"
      target: "${VSCODE_USER_DIR}/extensions"
      enabled: true
      priority: 2

# Homebrew configuration
homebrew:
  auto_update: true
  categories:
    core:
      enabled: true
      brewfile: "homebrew/Brewfile"
    apps:
      enabled: false
      brewfile: "homebrew/Brewfile.apps"
    dev:
      enabled: false
      brewfile: "homebrew/Brewfile.dev"
    mas:
      enabled: false
      brewfile: "homebrew/Brewfile.mas"

# Custom Applications
apps:
  vscode_extensions: 
    enabled: true
    scripts: 
      - "data/scripts/install_vscode_extensions.sh"
  macos_settings:
    enabled: true
    scripts:
      - "data/scripts/mac_settings.sh"

# Global Npm packages
npm:
  auto_install: true
  auto_update: true
  global_packages:
    - "@anthropic-ai/claude-code"
    - "@mariozechner/snap-happy"
    - "@google/gemini-cli"
    - "@vscode/vsce"

# Global UV packages
uv:
  auto_install: true
  auto_update: true
  global_packages:
    - "parllama"
```

#### ~/.config/dotfiles/themes.yaml
```yaml
themes:
  default:
    primary: "#007acc"
    secondary: "#00d7ff"
    success: "#00ff00"
    warning: "#ffaa00"
    error: "#ff0000"
    background: "#1e1e1e"
    foreground: "#ffffff"
  
  light:
    primary: "#0066cc"
    secondary: "#0099cc"
    success: "#008800"
    warning: "#cc6600"
    error: "#cc0000"
    background: "#ffffff"
    foreground: "#000000"
  
  cyberpunk:
    primary: "#ff007f"
    secondary: "#00ffff"
    success: "#00ff41"
    warning: "#ffaa00"
    error: "#ff073a"
    background: "#0d1117"
    foreground: "#00ff41"
```

### 3. Stow Linking Strategy & Behavior

#### How GNU Stow Works
GNU Stow creates symlinks from a **source package directory** to a **target directory** by mirroring the directory structure. The tool preserves the exact directory tree structure from the source, creating symlinks at the appropriate levels.

**Core Principle**: Each file/directory in the source package gets symlinked to the corresponding path in the target directory.

#### Package Structure → Target Mapping

**Source Package Structure**:
```
config/shell/          # Package directory
├── .zshrc            # Individual file
├── .zshprofile       # Individual file
└── .config/          # Directory
    └── starship.toml # Nested file
```

**Target Structure After Stow Linking** (target: `~/`):
```
~/                    # Target directory
├── .zshrc → config/shell/.zshrc           # Symlink to file
├── .zshprofile → config/shell/.zshprofile # Symlink to file
└── .config/          # Directory (may exist)
    └── starship.toml → config/shell/.config/starship.toml # Symlink to nested file
```

#### Concrete Package Examples

##### Shell Package Example
**Configuration**:
```yaml
- name: "shell"
  target: "~/"
  enabled: true
  priority: 2
```

**Source Structure**:
```
config/shell/
├── .zshrc
├── .zshprofile
├── .aliases
└── .config/
    ├── starship.toml
    └── zsh/
        └── functions.zsh
```

**Result After Linking**:
```
~/
├── .zshrc → ~/dev/dotfiles/config/shell/.zshrc
├── .zshprofile → ~/dev/dotfiles/config/shell/.zshprofile
├── .aliases → ~/dev/dotfiles/config/shell/.aliases
└── .config/
    ├── starship.toml → ~/dev/dotfiles/config/shell/.config/starship.toml
    └── zsh/
        └── functions.zsh → ~/dev/dotfiles/config/shell/.config/zsh/functions.zsh
```

##### Obsidian Package Example
**Configuration**:
```yaml
- name: "obsidian"
  target: "~/$OBSIDIAN_VAULT_DIR/"
  enabled: true
  priority: 7
```

**Source Structure**:
```
config/obsidian/
└── .obsidian/
    ├── config.json
    ├── workspace
    └── plugins/
        └── plugin-config.json
```

**Environment Variable Resolution**: `$OBSIDIAN_VAULT_DIR` → `/Users/username/Documents/MyVault`

**Result After Linking**:
```
/Users/username/Documents/MyVault/
└── .obsidian → ~/dev/dotfiles/config/obsidian/.obsidian
    ├── config.json (accessible via symlink)
    ├── workspace (accessible via symlink)
    └── plugins/ (accessible via symlink)
        └── plugin-config.json (accessible via symlink)
```

##### Config Package Example
**Configuration**:
```yaml
- name: "config"
  target: "~/.config"
  enabled: true
  priority: 1
```

**Source Structure**:
```
config/config/        # Note: This maps to current config/ directory
├── nvim/
│   └── init.vim
├── git/
│   └── config
└── tmux/
    └── tmux.conf
```

**Result After Linking**:
```
~/.config/
├── nvim/
│   └── init.vim → ~/dev/dotfiles/config/config/nvim/init.vim
├── git/
│   └── config → ~/dev/dotfiles/config/config/git/config
└── tmux/
    └── tmux.conf → ~/dev/dotfiles/config/config/tmux/tmux.conf
```

#### Environment Variable Expansion

**Supported Variables**:
- `$VSCODE_USER_DIR` - VS Code user directory
- `$OBSIDIAN_VAULT_DIR` - Obsidian vault directory
- `$HOME` or `~` - User home directory
- Any custom environment variables

**Expansion Rules**:
1. Variables are expanded at runtime before stow execution
2. Undefined variables cause validation errors
3. Variables can be set in shell environment or dotfiles config
4. Tilde (`~`) is always expanded to `$HOME`

**Example Expansion**:
```yaml
# Before expansion
target: "~/$VSCODE_USER_DIR/User"

# After expansion (macOS)
target: "/Users/username/Library/Application Support/Code/User"

# After expansion (Linux)
target: "/home/username/.config/Code/User"
```

#### Conflict Resolution Strategy

**When Target Files/Directories Already Exist**:

1. **File Conflicts**:
   ```bash
   # Existing file
   ~/.zshrc (regular file)
   
   # Stow behavior with backup enabled
   ~/.zshrc.backup      # Original file backed up
   ~/.zshrc → config/shell/.zshrc  # Symlink created
   ```

2. **Directory Conflicts**:
   ```bash
   # Existing directory with files
   ~/.config/nvim/init.vim (regular file)
   
   # Stow behavior (safe merge)
   ~/.config/nvim/init.vim.backup  # Original backed up
   ~/.config/nvim/ → config/config/nvim/  # Directory symlinked
   ```

3. **Symlink Conflicts**:
   ```bash
   # Existing symlink to different location
   ~/.zshrc → /old/location/.zshrc
   
   # Stow behavior
   ~/.zshrc.backup → /old/location/.zshrc  # Old symlink backed up
   ~/.zshrc → config/shell/.zshrc          # New symlink created
   ```

#### Priority-Based Execution

**Packages are processed in priority order** (lower numbers first):

```yaml
stow:
  packages:
    - name: "config"     # Priority 1 - Linked first
      target: "~/.config"
      priority: 1
    - name: "shell"      # Priority 2 - Linked second
      target: "~/"
      priority: 2
    - name: "git"        # Priority 3 - Linked third
      target: "~/"
      priority: 3
```

**Why Priority Matters**:
- Prevents conflicts between packages targeting overlapping directories
- Ensures critical configurations are linked first
- Allows dependent packages to override base configurations

#### Package Structure Requirements

**For Stow Tool Implementation**:

1. **Package Directory Naming**: Must match the `name` field in configuration
2. **Source Structure**: Directory tree under `config/{package_name}/` mirrors desired target structure
3. **File Permissions**: Preserved through symlinks
4. **Hidden Files**: Dotfiles (starting with `.`) are handled normally
5. **Nested Directories**: Full directory trees are supported

**Invalid Package Structures**:
```bash
# ❌ Wrong: Files at package root when target is not parent
config/shell/zshrc    # Missing dot prefix for home directory

# ✅ Correct: Proper dotfile naming
config/shell/.zshrc   # Will link to ~/.zshrc
```

### 4. Dynamic Directory Mapping

The refactor will reorganize the current repository structure to align with the new tool-based architecture:

#### Current → New Directory Mappings
```
# Configuration files (stow packages)
config/     → config/config/    # Current config/ becomes stow package
shell/      → config/shell/     # Move shell configs into config dir
git/        → config/git/       # Move git configs into config dir  
docker/     → config/docker/    # Move docker configs into config dir
warp/       → config/warp/      # Move warp configs into config dir
vivaldi/    → config/vivaldi/   # Move vivaldi configs into config dir
vscode/     → config/vscode/    # Move vscode configs into config dir
obsidian/   → config/obsidian/  # Move obsidian configs into config dir

# Data files (non-stow, rsync targets)
ai_docs/    → data/ai_docs/     # Move AI docs to data directory
specs/      → data/specs/       # Move specs to data directory
claude/     → data/claude/      # Move claude files to data directory

# Scripts and utilities
scripts/    → data/scripts/     # Move utility scripts to data directory
bin/        → data/bin/         # Move binary scripts to data directory

# Homebrew remains in place
homebrew/   → homebrew/         # Keep homebrew files in current location

# New Go application structure
(new)       → cmd/              # CLI entry point
(new)       → internal/         # Internal Go packages
(new)       → pkg/              # Public Go packages  
(new)       → test/             # Test files
(new)       → templates/        # Configuration templates
```

### 5. CLI Interface Design

#### Command Structure
```bash
# Main command
dotfiles [global-flags] <tool> <action> [tool-flags] [args]

# Global flags
--config string     Config file path (default: ~/.config/dotfiles/config.yaml)
--dry-run          Show what would be done without executing
--verbose          Enable verbose output
--yes              Answer yes to all prompts
--no-color         Disable colored output

# Tool Commands (dynamically generated from config)
dotfiles bootstrap     # Interactive bootstrap wizard
dotfiles tui           # Launch TUI interface
dotfiles stow          # Manage stow packages
dotfiles rsync         # Manage rsync operations
dotfiles brew          # Manage homebrew packages
dotfiles npm           # Manage npm global packages
dotfiles uv            # Manage uv tool packages
dotfiles apps          # Manage custom applications
dotfiles sync          # Sync all enabled tools
dotfiles status        # Show current status of all tools
dotfiles config        # Manage configuration
dotfiles clean         # Clean up old files
dotfiles test          # Run configuration tests
```

#### Dynamic Subcommand Examples
```bash
# Stow management
dotfiles stow link --packages config,shell
dotfiles stow unlink --packages git
dotfiles stow status
dotfiles stow list

# Rsync operations
dotfiles rsync sync --sources claude
dotfiles rsync status
dotfiles rsync list

# Homebrew management
dotfiles brew install --category core,dev
dotfiles brew update
dotfiles brew cleanup
dotfiles brew status

# NPM global packages
dotfiles npm install --packages claude-code
dotfiles npm update
dotfiles npm list
dotfiles npm status

# UV tool packages
dotfiles uv install --packages parllama
dotfiles uv update
dotfiles uv list
dotfiles uv status

# Custom applications
dotfiles apps run vscode_extensions
dotfiles apps run macos_settings
dotfiles apps status

# Configuration management
dotfiles config get global.log_level
dotfiles config set npm.auto_update true
dotfiles config edit
dotfiles config validate
dotfiles config reset

# Bootstrap operations
dotfiles bootstrap --interactive
dotfiles bootstrap --preset minimal
dotfiles bootstrap --tools stow,homebrew,npm
```

### 6. TUI Interface Design

#### Main Menu Structure (Dynamic Tool-Based)
```
┌─ Dotfiles Manager ─────────────────────────────────────────┐
│                                                            │
│  🏠 Overview          📊 Current system status            │
│  📦 Stow              🔗 Manage symlinked packages        │
│  📋 Rsync             🚀 Manage file synchronization      │
│  🍺 Homebrew          📦 Package management               │
│  📱 NPM               🌐 Global Node.js packages          │
│  🐍 UV                🛠️  Python tool packages            │
│  ⚙️  Apps              🔧 Custom application scripts      │
│  🎨 Themes            🖌️  UI customization                │
│  ⚙️  Settings          ⚙️  Configuration management        │
│  🧹 Maintenance       🗑️  Cleanup and testing            │
│                                                            │
│  Press Enter to select, q to quit, ? for help            │
└────────────────────────────────────────────────────────────┘
```

#### Tool Management Screen (Example: Stow)
```
┌─ Stow Package Management ──────────────────────────────────┐
│                                                            │
│  Package Status:                                           │
│  ✅ config     (→ ~/.config)         Priority: 1         │
│  ✅ shell      (→ ~/)               Priority: 2         │
│  ✅ git        (→ ~/)               Priority: 3         │
│  ❌ docker     (→ ~/)               Priority: 4         │
│  ✅ warp       (→ ~/)               Priority: 5         │
│  ✅ vscode     (→ $VSCODE_USER_DIR/) Priority: 6         │
│  ❌ obsidian   (→ $OBSIDIAN_VAULT/)  Priority: 7         │
│  ✅ ai_docs    (→ ~/dev/ai_docs)     Priority: 8         │
│  ✅ specs      (→ ~/dev/specs)       Priority: 9         │
│                                                            │
│  Actions:                                                  │
│  [L] Link selected packages                                │
│  [U] Unlink selected packages                              │
│  [R] Re-link all packages                                  │
│  [S] Show package details                                  │
│  [E] Edit package configuration                            │
│                                                            │
│  Use ↑/↓ to navigate, Space to select, Enter to confirm   │
└────────────────────────────────────────────────────────────┘
```

#### Tool Management Screen (Example: NPM)
```
┌─ NPM Global Package Management ────────────────────────────┐
│                                                            │
│  Global Packages:                                          │
│  ✅ @anthropic-ai/claude-code    v2.1.0    (up to date)  │
│  ❌ @mariozechner/snap-happy      -        (not installed)│
│  ✅ @google/gemini-cli           v1.5.2    (update avail.)│
│  ✅ @vscode/vsce                 v2.15.0   (up to date)   │
│                                                            │
│  Auto-install: ✅ Enabled                                  │
│  Auto-update:  ✅ Enabled                                  │
│                                                            │
│  Actions:                                                  │
│  [I] Install selected packages                             │
│  [U] Update selected packages                              │
│  [R] Remove selected packages                              │
│  [A] Install all packages                                  │
│  [S] Show package details                                  │
│                                                            │
│  Use ↑/↓ to navigate, Space to select, Enter to confirm   │
└────────────────────────────────────────────────────────────┘
```

#### Tool Management Screen (Example: UV)
```
┌─ UV Tool Package Management ───────────────────────────────┐
│                                                            │
│  UV Tools:                                                 │
│  ✅ parllama             v1.2.3    (up to date)           │
│                                                            │
│  Auto-install: ✅ Enabled                                  │
│  Auto-update:  ✅ Enabled                                  │
│                                                            │
│  Actions:                                                  │
│  [I] Install selected tools                                │
│  [U] Update selected tools                                 │
│  [R] Remove selected tools                                 │
│  [A] Install all tools                                     │
│  [S] Show tool details                                     │
│  [+] Add new tool                                          │
│                                                            │
│  Use ↑/↓ to navigate, Space to select, Enter to confirm   │
└────────────────────────────────────────────────────────────┘
```

### 7. Core Components Implementation

#### Dynamic Tool Interface
```go
// Tool interface that all tools must implement
type Tool interface {
    Name() string
    IsEnabled() bool
    Validate() error
    Status() (ToolStatus, error)
    Install(items []string) error
    Update(items []string) error
    Remove(items []string) error
    List() ([]ToolItem, error)
    Sync() error
}

// Tool registry for dynamic tool management
type ToolRegistry struct {
    tools map[string]Tool
}
```

#### Configuration Manager
- YAML configuration parsing and validation
- Hot-reloading of configuration changes
- Configuration migration handling
- Environment variable override support ($VSCODE_USER_DIR, etc.)
- CLI flag precedence management
- Dynamic tool configuration registration

#### Tool Implementations

##### Stow Tool
- **GNU Stow Command Wrapper**: Executes `stow --target={target} {package}` with proper error handling
- **Directory Structure Mirroring**: Preserves source package tree structure in target directory
- **Symlink Management**: Creates, updates, and removes symlinks according to package configuration
- **Environment Variable Expansion**: Resolves `$VSCODE_USER_DIR`, `$OBSIDIAN_VAULT_DIR`, etc. before execution
- **Priority-Based Execution**: Processes packages in configured priority order (1, 2, 3...)
- **Conflict Detection**: Identifies existing files/symlinks that would be overwritten
- **Backup Strategy**: Creates `.backup` files when `backup_enabled: true` in global config
- **Target Validation**: Ensures target directories exist or can be created
- **Package Structure Validation**: Verifies source package directory structure is valid
- **Rollback Capabilities**: Can unlink packages and restore backups if needed
- **Cross-Platform Compatibility**: Works on macOS and Linux with appropriate path handling

**Key Implementation Details**:
```go
type StowTool struct {
    config       *StowConfig
    dotfilesPath string
    backupSuffix string
}

// Core stow operations
func (s *StowTool) LinkPackage(packageName string) error {
    // 1. Resolve target path with environment variables
    // 2. Validate package directory exists
    // 3. Check for conflicts and create backups if needed
    // 4. Execute: stow --target={resolvedTarget} {packageName}
    // 5. Verify symlinks were created correctly
}

func (s *StowTool) UnlinkPackage(packageName string) error {
    // 1. Execute: stow --delete --target={resolvedTarget} {packageName}
    // 2. Restore backups if they exist
}
```

##### Rsync Tool  
- File synchronization operations
- Backup before sync
- Selective sync based on configuration
- Progress tracking for large operations
- Conflict resolution strategies

##### Homebrew Tool
- Brewfile management across categories
- Dependency resolution
- Update and cleanup operations
- MAS (Mac App Store) integration
- Bundle backup and restore

##### NPM Tool
- Global package management
- Version checking and updates
- Package installation verification
- Auto-install/update based on configuration
- Node.js version compatibility checks

##### UV Tool
- Python tool package management via `uv tool install`
- Tool environment isolation
- Version management
- Dependency resolution
- Tool listing and status checking

##### Apps Tool
- Custom script execution
- Script dependency checking
- Execution environment setup
- Output capturing and logging
- Script status and health checks

#### TUI Framework
- Bubbletea-based interactive interface
- Dynamic screen generation based on enabled tools
- Model-View-Update architecture
- Reusable UI components (lists, forms, dialogs)
- Tool-specific navigation and actions
- Keyboard shortcut management
- Progress indication and async operations
- Real-time status updates

#### CLI Command System
- Cobra-based command structure with dynamic tool commands
- Consistent flag handling across all tools
- Auto-generated help and completion
- Tool-agnostic command patterns
- Error handling and user feedback
- Integration with TUI for complex operations

### 8. Migration Strategy

#### Phase 1: Foundation & Tool Interface
1. Set up Go project structure
2. Implement dynamic tool interface and registry
3. Create basic configuration system with tool registration
4. Implement Stow tool as reference implementation
5. Create basic CLI framework with dynamic command generation

#### Phase 2: Core Tool Implementations  
1. Implement Rsync tool integration
2. Migrate Homebrew tool from bash scripts
3. Implement NPM tool based on `scripts/setup_npm_globals.sh`
4. Implement UV tool for Python package management
5. Implement Apps tool for custom script execution
6. Create basic TUI structure with dynamic tool screens

#### Phase 3: Directory Restructuring
1. Reorganize repository according to new structure mapping
2. Move configuration files to `config/` directory
3. Move data files to `data/` directory  
4. Update stow package configurations with new targets
5. Test all tools with new directory structure

#### Phase 4: Advanced Features & Polish
1. Complete TUI implementation with tool-specific screens
2. Add comprehensive testing framework
3. Implement theme and customization support
4. Performance optimization
5. Documentation and migration guides
6. Automated migration tools for existing users

#### Directory Restructuring Plan
```bash
# Step 1: Create new directory structure
mkdir -p cmd/dotfiles internal/{config,tools,tui,cli,engine,utils,types} pkg/dotfiles test/{integration,fixtures} templates docs

# Step 2: Move configuration files (create stow packages)
mkdir -p config/{config,shell,git,docker,warp,vivaldi,vscode,obsidian}
mv config/* config/config/     # Current config/ becomes config/config/ package
mv shell/* config/shell/
mv git/* config/git/
mv docker/* config/docker/
mv warp/* config/warp/
mv vivaldi/* config/vivaldi/
mv vscode/* config/vscode/
mv obsidian/* config/obsidian/

# Step 3: Move data files
mkdir -p data/{ai_docs,specs,claude,scripts,bin}
mv ai_docs/* data/ai_docs/
mv specs/* data/specs/
mv claude/* data/claude/
mv scripts/* data/scripts/
mv bin/* data/bin/

# Step 4: Clean up old directories
rm -rf shell git docker warp vivaldi vscode obsidian ai_docs specs claude scripts bin

# Step 5: Update stow package references in configuration
# This will be handled by the migration tool
```

## How to Test Changes

### 1. Unit Testing Strategy

#### Configuration Testing
```go
func TestConfigValidation(t *testing.T) {
    tests := []struct {
        name   string
        config string
        valid  bool
    }{
        {"valid_config_all_tools", validYAML, true},
        {"invalid_syntax", invalidYAML, false},
        {"missing_required_global", incompleteYAML, false},
        {"invalid_tool_config", invalidToolYAML, false},
        {"env_var_expansion", envVarYAML, true},
    }
    // Test implementation
}
```

#### Dynamic Tool Testing
```go
func TestToolInterface(t *testing.T) {
    // Test tool registration and discovery
    // Test tool validation
    // Test tool status checking
    // Test tool installation/update/removal
    
    tools := []Tool{
        &StowTool{}, &RsyncTool{}, &HomebrewTool{},
        &NPMTool{}, &UVTool{}, &AppsTool{},
    }
    
    for _, tool := range tools {
        t.Run(tool.Name(), func(t *testing.T) {
            testToolImplementation(t, tool)
        })
    }
}
```

#### NPM Tool Testing
```go
func TestNPMTool(t *testing.T) {
    // Test npm global package management
    // Test package installation verification
    // Test version checking and updates
    // Test Node.js compatibility
    // Reference: scripts/setup_npm_globals.sh behavior
}
```

#### UV Tool Testing
```go
func TestUVTool(t *testing.T) {
    // Test UV tool package management
    // Test tool environment isolation
    // Test version management
    // Test tool listing and status
}
```

#### CLI Command Testing
```go
func TestDynamicCLICommands(t *testing.T) {
    // Test dynamic command generation based on enabled tools
    // Test tool-specific command parsing
    // Test flag handling across all tools
    // Test output formatting consistency
    // Test error conditions for each tool
}
```

### 2. Integration Testing

#### End-to-End Bootstrap Testing
```bash
#!/bin/bash
# Create test environment
setup_test_env() {
    export HOME="/tmp/dotfiles-test-$$"
    mkdir -p "$HOME"
    # Set up minimal test environment with tool prerequisites
    setup_mock_tools
}

# Test full bootstrap process with all tools
test_bootstrap() {
    ./dotfiles bootstrap --dry-run --tools stow,homebrew,npm,uv
    assert_success "Bootstrap dry-run should succeed"
    
    ./dotfiles bootstrap --yes --preset minimal
    assert_success "Minimal bootstrap should succeed"
    
    verify_all_tools_status
    verify_configs_linked
    verify_packages_installed
}
```

#### Multi-Tool Integration Tests
```bash
test_all_tool_operations() {
    # Test Stow operations
    ./dotfiles stow link --packages config,shell
    assert_linked "$HOME/.config"
    assert_linked "$HOME/.zshrc"
    
    # Test Rsync operations  
    ./dotfiles rsync sync --sources claude
    assert_synced "$HOME/claude"
    
    # Test NPM operations
    ./dotfiles npm install --packages @anthropic-ai/claude-code
    assert_npm_installed "@anthropic-ai/claude-code"
    
    # Test UV operations
    ./dotfiles uv install --packages parllama
    assert_uv_installed "parllama"
    
    # Test Homebrew operations
    ./dotfiles brew install --category core
    assert_brew_packages_installed
    
    # Test Apps operations
    ./dotfiles apps run vscode_extensions
    assert_success "Apps script execution should succeed"
    
    # Test conflict resolution across tools
    test_cross_tool_conflicts
}

test_cross_tool_conflicts() {
    # Test handling conflicts between stow and rsync
    echo "conflict" > "$HOME/.gitconfig"
    ./dotfiles stow link --packages git
    assert_backup_created "$HOME/.gitconfig.backup"
    
    # Test tool priority handling
    ./dotfiles sync --all
    verify_tool_execution_order
}
```

### 3. TUI Testing Strategy

#### Dynamic Screen Testing
```go
func TestDynamicTUIScreens(t *testing.T) {
    // Test dynamic screen generation based on enabled tools
    // Test tool-specific screen rendering
    // Test navigation between tool screens
    // Test keyboard shortcuts consistency across tools
    
    enabledTools := []string{"stow", "npm", "uv", "homebrew"}
    for _, tool := range enabledTools {
        t.Run(fmt.Sprintf("screen_%s", tool), func(t *testing.T) {
            testToolScreen(t, tool)
        })
    }
}
```

#### Tool-Specific TUI Testing
```go
func TestNPMTUIScreen(t *testing.T) {
    // Test NPM package listing in TUI
    // Test package selection and actions
    // Test auto-install/update toggle behavior
    // Test real-time status updates
}

func TestUVTUIScreen(t *testing.T) {
    // Test UV tool listing in TUI
    // Test tool installation interface
    // Test version display and management
    // Test add new tool functionality
}

func TestStowTUIScreen(t *testing.T) {
    // Test package listing with priority display
    // Test target directory display
    // Test package selection and linking
    // Test conflict resolution interface
}
```

#### Screen Flow Testing
```go
func TestScreenNavigation(t *testing.T) {
    // Test main menu generation based on config
    // Test screen transitions between tools
    // Test state preservation across navigation
    // Test error handling and recovery in TUI
    // Test tool-specific help screens
}
```

### 4. Performance Testing

#### Benchmark Tests
```go
func BenchmarkConfigLoad(b *testing.B) {
    for i := 0; i < b.N; i++ {
        cfg, err := config.Load("test-config.yaml")
        if err != nil {
            b.Fatal(err)
        }
        _ = cfg
    }
}
```

#### Memory Usage Testing
```bash
# Test memory usage during operations
test_memory_usage() {
    local pid
    ./dotfiles tui &
    pid=$!
    
    # Monitor memory usage over time
    monitor_memory $pid
    
    kill $pid
}
```

### 5. Compatibility Testing

#### Cross-Platform Testing
```go
func TestCrossPlatform(t *testing.T) {
    if runtime.GOOS == "darwin" {
        testMacOSSpecific(t)
    }
    if runtime.GOOS == "linux" {
        testLinuxSpecific(t)
    }
}
```

#### Stow Version Compatibility
```bash
test_stow_versions() {
    for version in "2.3.1" "2.4.0" "latest"; do
        install_stow_version $version
        run_stow_tests
    done
}
```

## Self Validation

### 1. Functional Validation Checklist

- [ ] **Configuration Management**
  - [ ] YAML config loads correctly
  - [ ] Config validation catches errors
  - [ ] Hot-reloading works
  - [ ] CLI overrides function
  - [ ] Theme switching works

- [ ] **Tool Integration**
  - [ ] All 6 tools (stow, rsync, homebrew, npm, uv, apps) work correctly
  - [ ] Dynamic tool registration and discovery
  - [ ] Tool priority and execution order
  - [ ] Cross-tool conflict detection and resolution
  - [ ] Tool-specific configurations load properly
  - [ ] Environment variable expansion ($VSCODE_USER_DIR, etc.)

- [ ] **CLI Interface**
  - [ ] All commands work as expected
  - [ ] Help system is comprehensive
  - [ ] Error messages are clear
  - [ ] Dry-run mode works correctly
  - [ ] Completion works

- [ ] **TUI Interface**
  - [ ] Dynamic screen generation for enabled tools
  - [ ] All tool screens are navigable
  - [ ] Keyboard shortcuts work consistently
  - [ ] Visual feedback is clear
  - [ ] Real-time status updates work
  - [ ] Performance is acceptable
  - [ ] Tool-specific actions function correctly

- [ ] **Bootstrap Process**
  - [ ] Can bootstrap fresh system
  - [ ] Minimal preset works
  - [ ] Full preset works
  - [ ] Error recovery works
  - [ ] Progress indication works

### 2. Performance Validation

- [ ] **Startup Time**
  - [ ] CLI commands start in <100ms
  - [ ] TUI loads in <500ms
  - [ ] Config loading is fast
  - [ ] No unnecessary delays

- [ ] **Memory Usage**
  - [ ] CLI uses <50MB RAM
  - [ ] TUI uses <100MB RAM
  - [ ] No memory leaks
  - [ ] Efficient data structures

- [ ] **Responsiveness**
  - [ ] TUI responds to input quickly
  - [ ] Long operations show progress
  - [ ] Non-blocking where possible
  - [ ] Graceful handling of interrupts

### 3. User Experience Validation

- [ ] **Discoverability**
  - [ ] Features are easy to find
  - [ ] Help is contextual
  - [ ] Error messages guide users
  - [ ] Consistent UI patterns

- [ ] **Accessibility**
  - [ ] Keyboard navigation works
  - [ ] Color-blind friendly
  - [ ] Screen reader compatible
  - [ ] High contrast mode

- [ ] **Documentation**
  - [ ] Installation guide is clear
  - [ ] Migration guide exists
  - [ ] Command reference complete
  - [ ] Examples are helpful

### 4. Code Quality Validation

- [ ] **Test Coverage**
  - [ ] >90% unit test coverage
  - [ ] Integration tests pass
  - [ ] End-to-end tests pass
  - [ ] Performance tests pass

- [ ] **Code Standards**
  - [ ] Follows Go conventions
  - [ ] Consistent error handling
  - [ ] Proper logging
  - [ ] Clear documentation

- [ ] **Security**
  - [ ] No hardcoded secrets
  - [ ] Safe file operations
  - [ ] Input validation
  - [ ] Secure defaults

## Readme Clean

### New Repository Structure

The refactored repository will have a clean, modern README.md:

```markdown
# 🎯 Dotfiles Manager

A modern, interactive CLI tool for managing your dotfiles with ease. Built with Go and featuring a beautiful TUI interface powered by Bubbletea.

## ✨ Features

- 🖥️ **Dual Interface**: Use as CLI tool or interactive TUI
- 📦 **Smart Package Management**: Leverage GNU Stow with intelligent conflict resolution
- 🎨 **Themeable**: Customize the interface to match your style
- ⚡ **Fast & Reliable**: Written in Go for performance and reliability
- 🔧 **Highly Configurable**: Every aspect can be configured via YAML, UI, or CLI
- 🧪 **Testing Support**: Dry-run mode and comprehensive testing
- 💻 **Cross-Platform**: Works on macOS and Linux

## 🚀 Quick Start

### Install from Release
```bash
# Download latest release
curl -sf https://gobinaries.com/mbastakis/dotfiles | sh

# Or install with Go
go install github.com/mbastakis/dotfiles/cmd/dotfiles@latest
```

### Bootstrap Your System
```bash
# Interactive setup
dotfiles bootstrap

# Or quick setup with defaults
dotfiles bootstrap --preset minimal --yes
```

### Launch TUI
```bash
dotfiles tui
```

## 📖 Usage

### CLI Mode
```bash
# Link all packages
dotfiles stow link --all

# Install homebrew packages
dotfiles brew install --category core,dev

# Show current status
dotfiles status

# Update everything
dotfiles sync
```

### TUI Mode
Launch the interactive interface with `dotfiles tui` and navigate using:
- `↑/↓` or `j/k`: Navigate
- `Enter`: Select/Confirm
- `Space`: Toggle selection
- `Tab`: Switch panels
- `q`: Quit
- `?`: Help

## ⚙️ Configuration

Configuration is stored in `~/.config/dotfiles/config.yaml`. You can:
- Edit directly: `dotfiles config edit`
- Get values: `dotfiles config get global.log_level`
- Set values: `dotfiles config set homebrew.auto_update true`
- Validate: `dotfiles config validate`

## 🎨 Themes

Customize the appearance by editing `~/.config/dotfiles/themes.yaml` or use the TUI theme selector.

## 🧪 Testing

```bash
# Test your configuration
dotfiles test

# Dry run any operation
dotfiles --dry-run bootstrap --all

# Validate configuration
dotfiles config validate
```

## 📚 Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [Migration from v1](docs/migration.md)
- [Development Setup](docs/development.md)
- [Contributing](docs/contributing.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing.md).

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.
```

### Migration Documentation

Create `docs/migration.md` with guidance for users migrating from the bash-based system:

```markdown
# Migration from Bash-Based Dotfiles

This guide helps you migrate from the previous bash-script based dotfiles system to the new Go-based TUI tool.

## Automatic Migration

The new tool can automatically detect and migrate your existing configuration:

```bash
dotfiles migrate --from-bash --backup
```

## Manual Migration Steps

1. **Backup Current Setup**
2. **Install New Tool**
3. **Import Configuration**
4. **Verify Migration**
5. **Clean Up Old Scripts**

[Detailed steps...]
```

### Development Documentation

Create comprehensive development documentation including:
- Project structure explanation
- Development setup instructions
- Contributing guidelines
- Testing procedures
- Release process

This refactor transforms the dotfiles repository from a collection of bash scripts into a modern, maintainable, and user-friendly CLI/TUI application while preserving all existing functionality and adding powerful new features.
