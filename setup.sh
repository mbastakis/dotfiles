#!/bin/bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info "Starting dotfiles setup..."

# 1. Check and install Homebrew
if ! command -v brew &> /dev/null; then
    log_info "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for this session
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -f "/usr/local/bin/brew" ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    log_info "Homebrew is already installed"
fi

# 2. Check and install stow
if ! command -v stow &> /dev/null; then
    log_info "Installing stow..."
    brew update && brew upgrades
    brew install stow
else
    log_info "stow is already installed"
fi

# 3. Run stow
log_info "Running stow to create symlinks..."
cd "$SCRIPT_DIR"
stow .

# 4. Run nix installer
if [[ -f "$SCRIPT_DIR/bin/install_nix.sh" ]]; then
    log_info "Running Nix installer..."
    chmod +x "$SCRIPT_DIR/bin/install_nix.sh"
    "$SCRIPT_DIR/bin/install_nix.sh"
else
    log_warning "Nix installer not found at $SCRIPT_DIR/bin/install_nix.sh"
fi

log_info "Setup complete!"
