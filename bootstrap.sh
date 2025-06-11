#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit
source "$SCRIPT_DIR/scripts/utils.sh"

log_section "Starting Mac Setup"
log_info "This script will set up your Mac with your preferred configuration."

read -p "Do you want to proceed with the installation? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warning "Installation cancelled"
    exit 0
fi

log_section "Installing Homebrew"
bash "$SCRIPT_DIR/scripts/install_brew.sh"

log_section "Installing GNU Stow"
brew install stow

log_section "Linking Configuration Files"
log_info "Creating symlinks using stow..."

cd "$SCRIPT_DIR" || exit

# List of configurations to stow
configs=(
    "config"
    "shell"
    "git"
    "docker"
)

for config in "${configs[@]}"; do
    if [ -d "$config" ]; then
        log_info "Stowing $config"
        stow --adopt -v --no-folding -t "$HOME" "$config"
    else
        log_warning "Directory $config does not exist, skipping"
    fi
done

# Install Homebrew packages
log_section "Installing Homebrew Packages"
log_info "Installing essential packages..."
brew bundle --file="$SCRIPT_DIR/homebrew/Brewfile"

# Ask about GUI applications
read -p "Do you want to install GUI applications? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "$SCRIPT_DIR/homebrew/Brewfile.apps" ]; then
        log_info "Installing GUI applications..."
        brew bundle --file="$SCRIPT_DIR/homebrew/Brewfile.apps"
    else
        log_warning "Brewfile.apps not found, skipping GUI applications"
    fi
fi

# Ask about development tools
read -p "Do you want to install development tools? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "$SCRIPT_DIR/homebrew/Brewfile.dev" ]; then
        log_info "Installing development tools..."
        brew bundle --file="$SCRIPT_DIR/homebrew/Brewfile.dev"
    else
        log_warning "Brewfile.dev not found, skipping development tools"
    fi
fi

# Ask about Mac App Store applications
log_section "Installing Mac App Store Applications"
read -p "Do you want to install Mac App Store applications? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if user is signed in to Mac App Store
    mas_account=$(mas account 2>/dev/null || echo "")
    if [ -z "$mas_account" ]; then
        log_warning "You are not signed in to the Mac App Store"
        log_info "Please sign in to the Mac App Store and then run this script again"
        open -a "App Store"
        read -p "Press Enter when you have signed in to the Mac App Store... " -r
    fi
    
    if [ -f "$SCRIPT_DIR/homebrew/Brewfile.mas" ]; then
        log_info "Installing Mac App Store applications..."
        brew bundle --file="$SCRIPT_DIR/homebrew/Brewfile.mas"
    else
        log_warning "Brewfile.mas not found, skipping Mac App Store applications"
    fi
fi

# Apply macOS settings
log_section "Configuring macOS Settings"
read -p "Do you want to apply macOS settings? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    bash "$SCRIPT_DIR/scripts/mac_settings.sh"
fi

# Setup Obsidian configuration
log_section "Setting up Obsidian Configuration"
read -p "Do you want to setup Obsidian vault configuration syncing? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    bash "$SCRIPT_DIR/scripts/setup_obsidian.sh"
fi

log_section "Setup Complete!"
log_info "Your Mac has been configured successfully."
log_info "You may need to restart your Mac for some changes to take effect."
