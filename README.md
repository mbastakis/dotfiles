# Personal Dotfiles

A comprehensive macOS development environment featuring the BMad methodology, OpenCode AI agents, and modern development tooling.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/mbastakis/dotfiles.git ~/dotfiles
cd ~/dotfiles

# Run the automated setup
./setup.sh
```

This will install Homebrew, Nix Darwin, and use GNU Stow to symlink all configurations.

## 🎯 What's Included

### 🤖 AI-Powered Development
- **BMad Methodology**: Complete business methodology for agile development with 10 specialized agents
- **OpenCode Integration**: 22 AI agents for development tasks (architecture, product management, code review, etc.)
- **Claude AI Integration**: Advanced AI assistance with custom hooks and workflows

### 🛠️ Development Environment
- **Package Management**: Nix Darwin (170+ packages) + Homebrew
- **Shell**: Zsh with Starship prompt, Zinit plugins, Atuin history
- **Editors**: Neovim (Kickstart config), VS Code with extensions
- **Terminals**: Ghostty, Warp with 21 custom workflows
- **Git**: Multi-profile setup (personal/work) with enhanced tooling

### 🎨 UI & Productivity
- **Window Management**: AeroSpace tiling window manager
- **Menu Bar**: SketchyBar with custom widgets
- **Launcher**: Raycast with custom configurations
- **Knowledge Management**: Obsidian with 46 plugins and 9 themes

### 🔧 Development Tools
- **Containers**: Docker, Colima, Lazydocker, K9s
- **Languages**: Node.js, Python (pyenv), Go, Rust, Java, Lua
- **Databases**: PostgreSQL, Redis, MongoDB tools
- **Cloud**: AWS CLI, Terraform, kubectl

## 📁 Repository Structure

```
dotfiles/
├── 🎯 BMad Methodology
│   ├── dot-bmad-core/              # Core BMad framework
│   ├── dot-bmad-infrastructure-devops/ # Infrastructure extension
│   └── dot-claude/                 # Claude AI integration
├── 🤖 OpenCode Agents
│   └── dot-config/opencode/        # 22 specialized AI agents
├── ⚙️ System Configuration
│   ├── dot-config/nix-darwin/      # Nix package management
│   ├── dot-zsh/                    # Shell configuration
│   └── dot-config/*/               # Application configs
├── 🎨 UI & Productivity
│   ├── dot-warp/                   # Terminal workflows
│   ├── dot-obsidian/               # Knowledge management
│   └── dot-config/aerospace/       # Window management
└── 🔧 Setup & Utilities
    ├── setup.sh                    # Main installation script
    ├── bin/                        # Installation utilities
    └── .stowrc                     # Stow configuration
```

## 🎯 BMad Methodology

This repository includes a complete implementation of the **Business Methodology for Agile Development (BMad)**:

### Core Agents
- `@bmad-master` - Universal task executor
- `@business-analyst` - Requirements elicitation
- `@product-manager` - Product strategy and roadmap
- `@system-architect` - Technical architecture design
- `@senior-developer` - Implementation and code review

### Workflows
- **Greenfield**: New projects (Fullstack/Service/UI)
- **Brownfield**: Existing system enhancements

### Quality Gates
- Architect checklist
- Product manager checklist
- Story definition of done
- Change management process

**Learn more**: See `dot-bmad-core/user-guide.md` for complete documentation.

## 🤖 OpenCode AI Agents

22 specialized agents for development tasks:

```bash
# Core development
@system-architect     # Architecture design
@senior-developer     # Code implementation
@quality-assurance    # Testing and validation

# Product management
@product-manager      # Strategy and roadmap
@product-owner        # Backlog and stories
@scrum-master         # Process facilitation

# Research and analysis
@deep-researcher      # Comprehensive investigation
@business-analyst     # Requirements gathering
@context-primer       # Project analysis

# Optimization
@automation-orchestrator  # Workflow automation
@lean-optimizer           # Process optimization
@metrics-analyst          # Performance analysis

# And many more...
```

**Usage**: `@agent-name <your request>`

## 🔧 Key Features

### Automated Installation
- One-command setup with `./setup.sh`
- Handles Homebrew, Nix, and Stow automatically
- Installs 170+ packages and applications

### Multi-Environment Support
- Separate Git configurations for personal/work
- Environment-specific settings
- Flexible configuration management

### Advanced Shell Experience
- **Starship** prompt with Catppuccin theme
- **Atuin** for enhanced shell history
- **Zoxide** for smart directory navigation
- Custom aliases and functions

### Development Workflows
- **Warp Terminal**: 21 custom workflows for common tasks
- **Git Integration**: Enhanced with delta, lazygit, and custom hooks
- **Container Management**: Docker, K8s, and cloud tools
- **AI Assistance**: Integrated Claude and Fabric AI

## 📚 Documentation

- **BMad Guide**: `dot-bmad-core/user-guide.md`
- **OpenCode Agents**: `dot-config/opencode/AGENTS.md`
- **Brownfield Development**: `dot-bmad-core/working-in-the-brownfield.md`
- **Shell Configuration**: `dot-zsh/` directory

## 🛠️ Customization

### Personal Settings
1. Copy `dot-zsh/local.zsh.example` to `dot-zsh/local.zsh`
2. Add your personal environment variables and settings
3. Update Git configurations in `dot-gitconfig-personal`

### Adding New Configurations
1. Create new `dot-<appname>/` directory
2. Add configuration files
3. Run `stow dot-<appname>` to symlink

### Modifying Packages
- **Nix packages**: Edit `dot-config/nix-darwin/flake.nix`
- **Homebrew**: Edit `setup.sh` brew install commands

## 🔍 Troubleshooting

### Common Issues
- **Stow conflicts**: Remove existing dotfiles before running setup
- **Nix installation**: May require multiple attempts on first install
- **Permission issues**: Ensure proper file permissions for scripts

### Getting Help
- **BMad questions**: Use `@bmad-master` agent
- **OpenCode issues**: Check `dot-config/opencode/` configuration
- **Shell problems**: Review `dot-zsh/` files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test changes thoroughly
4. Submit a pull request

### Development Workflow
```bash
# Use BMad methodology for structured development
@bmad-master I want to enhance the dotfiles setup process

# Or work with specific agents
@system-architect Review the current architecture
@quality-assurance Validate my changes
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **BMad Methodology**: Business-driven development framework
- **OpenCode**: AI-powered development assistance
- **Nix Community**: Reproducible package management
- **Homebrew**: macOS package management
- **GNU Stow**: Symlink farm manager

---

**Note**: This is a personal dotfiles repository. Configurations are tailored for macOS development with specific tools and preferences. Feel free to fork and adapt for your own needs.
