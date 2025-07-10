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

# 5. Check and install VSCode extension
check_vscode_extension() {
    local extension_id="$1"
    if command -v code &> /dev/null; then
        # Check if extension is installed
        if code --list-extensions | grep -q "^${extension_id}$"; then
            return 0
        else
            return 1
        fi
    else
        log_warning "VSCode 'code' command not found"
        return 1
    fi
}

# Install TUI Manager extension
if command -v code &> /dev/null; then
    log_info "Checking VSCode extensions..."
    
    # Check if tui-manager extension is already installed
    if ! check_vscode_extension "local.tui-manager"; then
        log_info "TUI Manager extension not found. Installing..."
        
        # Run the extension installer script
        if [[ -f "$SCRIPT_DIR/bin/install_code_extensions.sh" ]]; then
            chmod +x "$SCRIPT_DIR/bin/install_code_extensions.sh"
            "$SCRIPT_DIR/bin/install_code_extensions.sh"
        else
            log_error "Extension installer script not found"
        fi
    else
        log_info "TUI Manager extension is already installed"
    fi
else
    log_warning "VSCode not found. Skipping extension installation"
fi

log_info "Setup complete!"
