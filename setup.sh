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
if ! command -v brew &>/dev/null; then
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
if ! command -v stow &>/dev/null; then
  log_info "Installing stow..."
  brew update && brew upgrades
  brew install stow
else
  log_info "stow is already installed"
fi

# 3. Run stow
log_info "Running stow to create symlinks..."
cd "$SCRIPT_DIR"
stow --adopt .

# 4. Run nix installer
if [[ -f "$SCRIPT_DIR/bin/install_nix.sh" ]]; then
  log_info "Running Nix installer..."
  chmod +x "$SCRIPT_DIR/bin/install_nix.sh"
  "$SCRIPT_DIR/bin/install_nix.sh"
else
  log_warning "Nix installer not found at $SCRIPT_DIR/bin/install_nix.sh"
fi

# 5. Install/upgrade Yazi plugins
if command -v ya &>/dev/null; then
  log_info "Installing/upgrading Yazi plugins..."
  ya pkg upgrade || ya pkg install 2>/dev/null || log_warning "Yazi plugin installation failed"
else
  log_warning "ya (Yazi CLI) not found, skipping plugin installation"
fi

# 6. Install LaunchAgents
LAUNCHAGENTS_SRC="$SCRIPT_DIR/dot-launchagents"
LAUNCHAGENTS_DST="$HOME/Library/LaunchAgents"

if [[ -d "$LAUNCHAGENTS_SRC" ]]; then
  mkdir -p "$LAUNCHAGENTS_DST"
  mkdir -p "$HOME/.local/share/opencode"  # For logs
  for plist in "$LAUNCHAGENTS_SRC"/*.plist; do
    if [[ -f "$plist" ]]; then
      plist_name="$(basename "$plist")"
      dst_file="$LAUNCHAGENTS_DST/$plist_name"
      label="${plist_name%.plist}"

      # Substitute __HOME__ placeholder with actual home directory
      tmp_plist=$(mktemp)
      sed "s|__HOME__|$HOME|g" "$plist" > "$tmp_plist"

      # Check if plist changed
      if [[ ! -f "$dst_file" ]] || ! cmp -s "$tmp_plist" "$dst_file"; then
        # Unload existing agent (idempotent - ignore errors if not loaded)
        launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true

        # Install and load new agent
        cp "$tmp_plist" "$dst_file"
        launchctl bootstrap "gui/$(id -u)" "$dst_file"
        log_info "Installed and loaded LaunchAgent: $plist_name"
      else
        # Ensure agent is loaded even if file unchanged
        if ! launchctl list | grep -q "$label"; then
          launchctl bootstrap "gui/$(id -u)" "$dst_file"
          log_info "Loaded LaunchAgent: $plist_name"
        else
          log_info "LaunchAgent up to date: $plist_name"
        fi
      fi

      rm -f "$tmp_plist"
    fi
  done
else
  log_info "No LaunchAgents to install"
fi

# 7. Install custom keyboard layouts
KEYBOARD_LAYOUTS_SRC="$SCRIPT_DIR/dot-config/keyboard-layouts"
KEYBOARD_LAYOUTS_DST="$HOME/Library/Keyboard Layouts"

if [[ -d "$KEYBOARD_LAYOUTS_SRC" ]]; then
  mkdir -p "$KEYBOARD_LAYOUTS_DST"
  layouts_changed=false
  for layout in "$KEYBOARD_LAYOUTS_SRC"/*.keylayout; do
    if [[ -f "$layout" ]]; then
      layout_name="$(basename "$layout")"
      dst_file="$KEYBOARD_LAYOUTS_DST/$layout_name"
      if [[ ! -f "$dst_file" ]] || ! cmp -s "$layout" "$dst_file"; then
        cp "$layout" "$KEYBOARD_LAYOUTS_DST/"
        log_info "Installed keyboard layout: $layout_name"
        layouts_changed=true
      fi
    fi
  done
  if [[ "$layouts_changed" == "true" ]]; then
    log_warning "You may need to log out and back in for new keyboard layouts to appear in System Settings"
  else
    log_info "Keyboard layouts are up to date"
  fi
fi

log_info "Setup complete!"
