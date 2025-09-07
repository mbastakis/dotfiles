# Personal Dotfiles Repository

A comprehensive macOS development environment configuration using GNU Stow, Nix Darwin, and extensive AI tooling integration.

## 🚀 Quick Start

```bash
# Clone repository
git clone <repo-url> ~/dev/dotfiles
cd ~/dev/dotfiles

# Run setup script (installs Homebrew, Stow, Nix)
./setup.sh

# Apply Nix Darwin configuration
cd dot-config/nix-darwin
darwin-rebuild switch --flake .#simple

# Install VS Code extensions (optional)
./bin/install_code_extensions.sh
```

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [AI Integration](#ai-integration)
- [Development Workflow](#development-workflow)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🎯 Overview

This dotfiles repository manages a sophisticated macOS development environment designed for:

- **AI-Enhanced Development**: Extensive integration with Claude, OpenCode, and Gemini
- **Productivity Optimization**: Custom workflows, automation, and keyboard-driven interfaces
- **Reproducible Setup**: Declarative configuration using Nix Darwin and GNU Stow
- **Consistent Theming**: Catppuccin Mocha theme across all applications

### Key Stakeholders
- Primary user: Software developer working across multiple projects
- Focus: AI-assisted development workflows and productivity optimization

## ✨ Features

### 🤖 AI-Powered Development
- **OpenCode Integration**: AI development environment with MCP servers
- **Context7**: Library documentation integration for better code understanding
- **Obsidian MCP**: Knowledge base integration for project documentation
- **Claude CLI**: Direct AI assistance in terminal workflows

### 🔧 Development Tools
- **Editor**: Neovim (Kickstart config) + VS Code with portable configuration
- **Terminal**: Warp with 20+ custom workflows + Ghostty as backup
- **Git**: Lazygit, Git Delta, GitHub CLI, GitLab CLI
- **Containers**: Docker, Colima, Lazydocker, K9s
- **File Management**: Yazi (terminal-based file manager)

### 🎨 Interface & Productivity
- **Window Manager**: AeroSpace (Dvorak-optimized tiling)
- **Status Bar**: SketchyBar with custom plugins
- **Shell**: Zsh with Zinit plugin manager and Starship prompt
- **Theme**: Consistent Catppuccin Mocha across all tools

### 📦 Package Management
- **Hybrid Approach**: Nix Darwin for system packages + Homebrew for GUI apps
- **Language Support**: Node.js, Go, Rust, Python, Java
- **Version Control**: All configurations tracked in Git

## 🏗️ Architecture

### Directory Structure
```
dotfiles/
├── dot-*                    # Stow packages (symlinked to ~)
│   ├── dot-config/          # Application configurations
│   ├── dot-claude/          # Claude AI integration
│   ├── dot-ai-core/         # AI workflow templates and agents
│   ├── dot-gemini/          # Gemini AI integration
│   ├── dot-obsidian/        # Obsidian configurations
│   ├── dot-warp/            # Warp terminal workflows
│   └── dot-zsh/             # Shell configurations
├── bin/                     # Installation scripts
├── setup.sh                # Main setup script
└── PROJECT_CONTEXT.md       # Detailed project documentation
```

### Configuration Modules

1. **Shell Environment** (`dot-zsh/`, `dot-zshrc`)
   - Custom aliases, functions, and exports
   - Plugin management with Zinit
   - Tool integrations (atuin, zoxide, starship)

2. **AI Integration** (`dot-ai-core/`, `dot-claude/`, `dot-gemini/`)
   - Agent prompts and task definitions
   - Development workflow automation
   - Knowledge base integration

3. **Development Tools** (`dot-config/`)
   - Editor configurations (Neovim, VS Code)
   - Git with conditional work/personal configs
   - Container and cloud tool setups

4. **System Configuration** (`dot-config/nix-darwin/`)
   - Declarative package management
   - System preferences and defaults
   - Homebrew integration

## 🔧 Installation

### Prerequisites
- macOS (Apple Silicon recommended)
- Xcode Command Line Tools
- Internet connection

### Automated Setup
```bash
# 1. Clone repository
git clone <repo-url> ~/dev/dotfiles
cd ~/dev/dotfiles

# 2. Run setup script
./setup.sh
```

The setup script will:
- Install Homebrew if not present
- Install GNU Stow and Nix
- Create necessary symlinks
- Set up basic shell configuration

### Manual Steps
```bash
# Apply Nix Darwin configuration
cd dot-config/nix-darwin
darwin-rebuild switch --flake .#simple

# Install VS Code extensions (optional)
./bin/install_code_extensions.sh

# Reload shell configuration
source ~/.zshrc
```

## ⚙️ Configuration

### Key Configuration Files
- **System**: `dot-config/nix-darwin/flake.nix`
- **Shell**: `dot-zshrc`, `dot-zsh/*.zsh`
- **Git**: `dot-gitconfig`, `dot-gitconfig-personal`, `dot-gitconfig-work`
- **AI Tools**: `dot-config/opencode/opencode.json`
- **Editor**: `dot-config/nvim/init.lua`
- **Window Manager**: `dot-config/aerospace/aerospace.toml`

### Environment Variables
```bash
EDITOR=code                    # Default editor
SHELL=/bin/zsh                # Default shell
HOMEBREW_PREFIX=/opt/homebrew  # Homebrew installation path
```

### Git Configuration
Conditional Git configurations for work and personal projects:
- Work repositories: Uses work email and signing key
- Personal repositories: Uses personal email and signing key

## 🚀 Usage

### Essential Commands
```bash
# Reload shell configuration
reload

# File navigation and search
l, ll, la, ld          # Enhanced ls with eza
r                      # Interactive history search with atuin
cd <path>              # Enhanced cd with zoxide

# Development tools
v <file>               # Open in Neovim
obs                    # Obsidian CLI
lazygit                # Git interface
k9s                    # Kubernetes interface

# AI development
opencode               # AI-powered development environment
claude-code            # Claude CLI integration
```

### Warp Workflows
The repository includes 20+ custom Warp workflows for common tasks:
- File and directory operations
- Git operations
- Docker and Kubernetes management
- System monitoring and maintenance
- AI tool integration

### Window Management (AeroSpace)
Dvorak-optimized keybindings for efficient window management:
- Workspace switching and window movement
- Tiling and floating window controls
- Multi-monitor support

## 🤖 AI Integration

### OpenCode Setup
The repository includes comprehensive OpenCode configuration with MCP servers:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "npx",
      "args": ["-y", "@executeautomation/mcp-obsidian"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"]
    }
  }
}
```

### AI Workflow Components
- **Agent Prompts**: Specialized prompts for different development tasks
- **Task Templates**: Reusable templates for common AI interactions
- **Checklist Systems**: Quality assurance and process checklists
- **Knowledge Integration**: Direct access to Obsidian notes and documentation

## 🔄 Development Workflow

### Making Changes
1. **Edit configurations** in the dotfiles repository
2. **Apply changes** with `stow .` for symlinks
3. **Update system** with `darwin-rebuild switch --flake .#simple` for Nix changes
4. **Commit and push** changes to Git
5. **Sync across machines** by pulling and re-running setup

### Package Management
```bash
# Update Homebrew packages
brew update && brew upgrade

# Update Nix packages
cd dot-config/nix-darwin
nix flake update
darwin-rebuild switch --flake .#simple

# Update shell plugins
zinit update
```

### Testing Configuration
- **Nix validation**: `nix flake check`
- **Stow verification**: Check for symlink conflicts
- **Tool integration**: Verify AI tools and MCP connections
- **Manual testing**: Test aliases, functions, and workflows

## 🎨 Customization

### Adding New Tools
1. Create configuration in appropriate `dot-config/` subdirectory
2. Add to Nix Darwin configuration if system package
3. Add to Homebrew if GUI application
4. Create aliases/functions in `dot-zsh/`
5. Update documentation

### Theming
All tools use the Catppuccin Mocha theme for consistency:
- Terminal applications
- Editors and IDEs
- System UI elements
- Custom themes in `dot-config/*/themes/`

### Custom Functions and Aliases
Add to `dot-zsh/`:
- `aliases.zsh`: Short command aliases
- `functions.zsh`: Complex shell functions
- `custom_shortcuts.zsh`: Workflow shortcuts

## 🔍 Troubleshooting

### Common Issues

**Stow conflicts**
```bash
# Remove conflicting files and re-run stow
stow --adopt .
```

**Nix Darwin build failures**
```bash
# Check flake syntax
nix flake check

# Clean build cache
nix store gc
```

**AI tool connection issues**
```bash
# Verify MCP server installation
npx -y @executeautomation/mcp-obsidian --version
npx -y @context7/mcp-server --version
```

### Getting Help
- Check `PROJECT_CONTEXT.md` for detailed architecture information
- Review tool-specific documentation in configuration files
- Use `opencode` for AI-assisted troubleshooting

## 🤝 Contributing

### Development Guidelines
- Follow existing naming conventions (`dot-*` directories)
- Maintain consistent theming (Catppuccin Mocha)
- Document significant changes
- Test configurations before committing

### Areas for Improvement
1. **Cross-platform support**: Extend to Linux/Windows
2. **Configuration templates**: Create reusable templates
3. **Automated testing**: Implement configuration validation
4. **Documentation**: Add inline comments to complex configs

## 📚 Resources

- **Nix Darwin**: [nix-darwin documentation](https://github.com/LnL7/nix-darwin)
- **GNU Stow**: [Stow manual](https://www.gnu.org/software/stow/manual/stow.html)
- **OpenCode**: [OpenCode documentation](https://opencode.ai)
- **AeroSpace**: [AeroSpace configuration](https://github.com/nikitabobko/AeroSpace)
- **Catppuccin**: [Theme documentation](https://catppuccin.com)

## 📄 License

This repository is for personal use. Feel free to fork and adapt for your own dotfiles setup.

---

**Note**: This is a living configuration that evolves with development needs. Regular updates and improvements are expected as new tools and workflows are adopted.