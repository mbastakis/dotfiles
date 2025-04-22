# 🚀 Mac Dotfiles

This repository contains my personal dotfiles and automation scripts for setting up a new macOS machine quickly and efficiently. Using GNU Stow, this repo creates symlinks from the home directory to the configuration files in this repo, allowing easy version control and synchronization across machines.

## 📦 What's Included

- **Shell Configuration**: ZSH setup with custom aliases, functions, and prompt
- **Plugin Management**: Zinit for managing ZSH plugins and extensions
- **macOS Settings**: Sensible defaults for macOS
- **Homebrew**: Package installation automation
- **App Configurations**: Settings for Raycast, Karabiner, and other tools
- **Custom Fonts**: JetBrains Mono and other typography
- **Development Environment**: Configuration for development tools

## 🔧 Installation

### Quick Install (Full Setup)

```bash
git clone https://github.com/yourusername/.dotfiles.git ~/.dotfiles
cd ~/.dotfiles
chmod +x bootstrap.sh
./bootstrap.sh
```

### Manual Installation (Pick and Choose)

If you want to set up specific components only:

1. **Install Homebrew**:

   ```bash
   ./scripts/install_brew.sh
   ```

2. **Install Core Packages**:

   ```bash
   brew bundle --file=./homebrew/Brewfile
   ```

3. **Install GUI Applications**:

   ```bash
   brew bundle --file=./homebrew/Brewfile.apps
   ```

4. **Install Development Tools**:

   ```bash
   brew bundle --file=./homebrew/Brewfile.dev
   ```

5. **Apply Configuration Files**:

   ```bash
   stow -v --target="$HOME" config shell bin
   ```

6. **Set macOS Defaults**:

   ```bash
   ./scripts/mac_settings.sh
   ```

7. **Install Mac App Store Applications**:

   ```bash
   brew bundle --file=./homebrew/Brewfile.mas
   ```

## 🛠 Customization

### How Stow Works

GNU Stow creates symlinks from your home directory to the files in this repository. The directory structure within each package (config, shell, bin) mirrors the structure that would exist in your home directory.

For example:

- `~/.dotfiles/config/.config/starship/starship.toml` becomes `~/.config/starship/starship.toml`
- `~/.dotfiles/shell/.zshrc` becomes `~/.zshrc`
- `~/.dotfiles/bin/update_dotfiles` becomes `~/bin/update_dotfiles`

### Adding Homebrew Packages

Edit the appropriate Brewfile:

- `homebrew/Brewfile` for essential utilities
- `homebrew/Brewfile.apps` for GUI applications
- `homebrew/Brewfile.dev` for development tools

### Adding App Configurations

1. Create a directory for your app in `config/.config/`
2. Add configuration files
3. Run `stow -v --target="$HOME" config` to create symlinks

### Customizing ZSH

- Add aliases to `shell/.zsh/aliases.zsh`
- Add exports to `shell/.zsh/exports.zsh`
- Add functions to `shell/.zsh/functions.zsh`
- Modify main configuration in `shell/.zshrc`
- Add ZSH plugins to `shell/.zsh/plugins.zsh`

### Managing ZSH Plugins with Zinit

This repository uses [Zinit](https://github.com/zdharma-continuum/zinit) for ZSH plugin management. Zinit is a flexible and fast plugin manager that offers features like turbo mode, completions management, and plugin analytics.

#### Adding New Plugins

To add a new plugin, edit `shell/.zsh/plugins.zsh` and add your plugin using one of these patterns:

```bash
# Simple plugin loading
zinit load username/repository

# Light mode (faster, without reporting or tracking)
zinit light username/repository

# Turbo mode (deferred loading for faster shell startup)
zinit wait lucid for username/repository

# More complex loading with ice modifiers
zinit ice wait"0" lucid
zinit load username/repository
```

#### Example Plugins

The configuration includes several useful plugins by default:

- Fast syntax highlighting
- ZSH completions
- Auto-suggestions
- History search multi-word

### Customizing Starship Prompt

Edit `config/.config/starship/starship.toml`

### Adding Custom Scripts

1. Add your script to the `bin/` directory
2. Make it executable with `chmod +x bin/your-script`
3. Run `stow -v --target="$HOME" bin` to create symlinks

### Adding macOS Settings

Edit `scripts/mac_settings.sh` to add or modify macOS defaults commands

## 🔄 Updating

To update your configuration after making changes:

```bash
cd ~/.dotfiles
git pull                           # Get latest changes
~/bin/update_dotfiles              # Re-stow all configurations
```

Alternatively, you can manually re-stow specific packages:

```bash
cd ~/.dotfiles
stow -v --restow --target="$HOME" config  # Refresh just config symlinks
```

## 📂 Repository Structure

```txt
.dotfiles/
├── README.md                  # Main documentation
├── bootstrap.sh               # Main installation script
├── bin/                       # Custom executable scripts
│   └── update_dotfiles        # Script to update dotfiles
├── config/                    # Directories organized by application
│   └── .config/
│       ├── aerospace/         # Aerospace window manager configuration
│       ├── karabiner/         # Karabiner keyboard customization
│       ├── raycast/           # Raycast launcher configuration
│       └── starship/          # Starship terminal prompt
│       └── .../               # Other ...
├── homebrew/
│   ├── Brewfile               # Core/essential applications
│   ├── Brewfile.apps          # GUI applications
│   ├── Brewfile.dev           # Development tools
│   └── Brewfile.mas           # Mac App Store
├── scripts/
│   ├── install_brew.sh        # Install Homebrew
│   ├── mac_settings.sh        # Configure macOS
│   └── utils.sh               # Shared utility functions
└── shell/
    ├── .zshrc                 # Main ZSH configuration
    └── .zsh/                  # ZSH component files
        ├── aliases.zsh        # Shell aliases
        ├── exports.zsh        # Environment variables
        ├── plugins.zsh        # Plugins for zsh
        └── functions.zsh      # Custom shell functions
```

## ⚠️ Warning

These dotfiles are personalized to my workflow. Review the code before installing, and modify to suit your needs.

## 📚 Resources

- [GNU Stow Documentation](https://www.gnu.org/software/stow/manual/stow.html)
- [Homebrew Documentation](https://docs.brew.sh)
- [Defaults documentation](https://macos-defaults.com/) - A comprehensive guide to macOS `defaults` commands
- [Defaults forum](https://www.defaults-write.com/) - Users sharing their defaults automation
