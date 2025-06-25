# Dotfiles Repository Context & Analysis

> **Generated on:** 2025-06-25  
> **Purpose:** Complete analysis of dotfiles repository structure for Claude Code reference

## Repository Overview

This dotfiles repository manages macOS system configuration using GNU Stow for symlink management and Homebrew for package installation. The repository is organized into modular components that can be installed independently or as a complete system.

## Current Architecture

### Core Components

1. **GNU Stow Configuration Management**
   - Symlinks configuration files from repo to home directory
   - Organized by application in `config/.config/`
   - Managed via `bin/manage_stow` script

2. **Homebrew Package Management**
   - Split into category-based Brewfiles:
     - `Brewfile` - Core/essential CLI tools
     - `Brewfile.apps` - GUI applications  
     - `Brewfile.dev` - Development tools
     - `Brewfile.mas` - Mac App Store apps
   - Managed via `bin/manage_brew` script

3. **Application-Specific Setup**
   - VS Code: Settings, keybindings, extensions via `bin/setup_vscode`
   - Obsidian: Vault configuration via `bin/setup_obsidian`
   - Git: Conditional configuration for work/personal contexts

### Installation Methods

1. **Full Setup**: `./bootstrap.sh --all`
2. **Selective Setup**: `./bootstrap.sh --dev --vscode`
3. **Manual**: Individual scripts and stow commands

## Current Tool Configurations

### Yazi File Manager

**Location:** `config/.config/yazi/`

**Current Plugin Status:**
- **Git Plugin:** `yazi-rs/plugins:git` (installed via `ya pkg`)
- **Catppuccin Themes:** Both Frappe and Mocha variants
- **Plugin Lock File:** `package.toml` with specific revisions and hashes

**Integration Points:**
- VS Code keybinding (Cmd+E) launches yazi
- Homebrew installation via `Brewfile`
- Custom keymaps for fzf, zoxide, ripgrep integration

**Plugin Installation Method:**
```bash
ya pkg add yazi-rs/plugins:git
ya pkg add yazi-rs/flavors:catppuccin-mocha
```

### Claude Code CLI

**Current Status:** Not integrated into dotfiles
**Manual Installation:** `npm i -g @anthropic-ai/claude-code`
**Update Method:** Manual `npm update -g @anthropic-ai/claude-code`

## Analysis Results

### Yazi Plugin Management

**Current Approach:**
- Plugins installed manually via `ya pkg` commands
- Configuration tracked in `package.toml` with version locking
- No automation for new machine setups

**Issues Identified:**
1. New machine setup requires manual plugin installation
2. No automated plugin updates
3. Plugin state not synchronized with dotfiles deployment

### Claude Code Integration

**Current Approach:**
- Manual NPM installation outside of dotfiles management
- No version tracking or automated updates
- Not integrated with existing Homebrew workflow

**Issues Identified:**
1. No Homebrew formula available for Claude Code
2. NPM global installation required
3. Manual update process
4. Not part of dotfiles automation

## Homebrew Management System

**Current Structure:**
- **Core Tools:** Essential CLI utilities, development tools, system utilities
- **GUI Apps:** Desktop applications, browsers, productivity tools
- **Dev Tools:** IDEs, programming languages, development utilities
- **MAS Apps:** Mac App Store applications

**Management Script:** `bin/manage_brew`
- Supports selective installation by category
- Handles brew bundle operations
- Includes update and cleanup functionality

## Recommendations Summary

### For Yazi Plugins:
1. Add automation script for plugin installation
2. Integrate with bootstrap process
3. Create update mechanism for plugins

### For Claude Code:
1. Add to Brewfile.dev as NPM package installation
2. Create update automation script
3. Document installation process

## Implementation Strategies

### Strategy 1: Yazi Plugin Automation

**Problem:** Yazi plugins are not automatically installed on new machine setups.

**Solution:** Create a setup script that automates yazi plugin installation.

**Implementation Plan:**
1. Create `bin/setup_yazi` script that:
   - Checks if yazi is installed
   - Creates yazi config directory if needed
   - Installs plugins using `ya pkg` commands
   - Links existing configuration via stow

2. Integrate with bootstrap.sh:
   - Add `--yazi` flag option
   - Include in `--all` installation
   - Add to selective installation documentation

3. Plugin Update Strategy:
   - Add update function to `bin/setup_yazi`
   - Include in `bin/update_dotfiles` script
   - Preserve existing `package.toml` version locking

**Script Structure:**
```bash
#!/bin/bash
# bin/setup_yazi - Yazi file manager setup and plugin management

setup_yazi_plugins() {
    if ! command -v ya &> /dev/null; then
        echo "Yazi (ya) not found. Installing via homebrew first..."
        brew install yazi
    fi
    
    echo "Installing yazi plugins..."
    ya pkg add yazi-rs/plugins:git
    ya pkg add yazi-rs/flavors:catppuccin-mocha
}
```

### Strategy 2: Claude Code CLI Integration

**Problem:** Claude Code CLI is not available via Homebrew and requires manual NPM installation.

**Solution:** Add NPM-based installation to development tools management.

**Implementation Plan:**
1. Add Claude Code to `Brewfile.dev` as a post-install script:
   ```bash
   # AI/ML Development Tools
   # Note: Claude Code installed via NPM (no Homebrew formula available)
   # Run: npm install -g @anthropic-ai/claude-code
   ```

2. Create `bin/setup_claude_code` script:
   - Check Node.js availability
   - Install Claude Code via NPM
   - Handle authentication setup
   - Provide update functionality

3. Integrate with existing workflow:
   - Add to bootstrap.sh as `--claude-code` option
   - Include in development tools documentation
   - Add to update automation

**Script Structure:**
```bash
#!/bin/bash
# bin/setup_claude_code - Claude Code CLI installation and management

install_claude_code() {
    if ! command -v node &> /dev/null; then
        echo "Node.js required for Claude Code. Install via brew first."
        exit 1
    fi
    
    echo "Installing Claude Code CLI..."
    npm install -g @anthropic-ai/claude-code
    
    echo "Claude Code installed. Run 'claude' to authenticate."
}

update_claude_code() {
    echo "Updating Claude Code CLI..."
    npm update -g @anthropic-ai/claude-code
}
```

### Strategy 3: Unified Update System

**Enhancement:** Create a centralized update system for all non-Homebrew tools.

**Implementation:**
1. Extend `bin/update_dotfiles` to include:
   - Yazi plugin updates
   - Claude Code CLI updates
   - VS Code extension updates (already exists)

2. Create modular update system:
   ```bash
   # bin/update_dotfiles additions
   update_yazi_plugins
   update_claude_code
   update_npm_packages
   ```

## Installation Commands After Implementation

### New Machine Setup:
```bash
# Full setup including new tools
./bootstrap.sh --all

# Selective setup
./bootstrap.sh --dev --yazi --claude-code
```

### Updates:
```bash
# Update everything including plugins
./bin/update_dotfiles

# Update specific tools
./bin/setup_yazi --update
./bin/setup_claude_code --update
```

## Benefits of This Approach

1. **Consistent with existing patterns** - Uses same script structure and naming conventions
2. **Modular installation** - Can install tools independently or together
3. **Automated updates** - Centralized update system handles all tools
4. **Documentation consistency** - Follows same help and documentation patterns
5. **Backwards compatible** - Doesn't break existing workflows