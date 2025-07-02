#!/usr/bin/env bash
#
# Yazi Packages Setup Script
# Installs essential Yazi plugins and themes using ya package manager
#
# Author: mbastakis
# Last updated: 2024-12-28
#

set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the shared utilities
source "$SCRIPT_DIR/utils.sh" 2>/dev/null || {
    # Fallback logging if utils.sh is not available
    log_info() { echo "[INFO] $1"; }
    log_error() { echo "[ERROR] $1" >&2; }
    log_success() { echo "[SUCCESS] $1"; }
    log_warning() { echo "[WARNING] $1" >&2; }
    log_section() { echo ""; echo "=== $1 ==="; echo ""; }
    log_subsection() { echo "--- $1 ---"; }
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main function
main() {
    local action="${1:-setup}"
    
    log_section "Yazi Packages Setup"
    
    # Check if yazi and ya are available
    check_yazi_available
    
    # Execute action
    case "$action" in
        "setup"|"install")
            install_yazi_packages
            ;;
        "update")
            update_yazi_packages
            ;;
        "plugins")
            install_yazi_plugins
            ;;
        "themes")
            install_yazi_themes
            ;;
        *)
            log_error "Unknown action: $action"
            log_info "Usage: $0 [setup|update|plugins|themes]"
            exit 1
            ;;
    esac
    
    log_success "Yazi packages setup complete"
}

# Check if yazi and ya are available
check_yazi_available() {
    if ! command_exists yazi; then
        log_error "Yazi not found. Please install yazi first:"
        log_info "  brew install yazi"
        exit 1
    fi
    
    if ! command_exists ya; then
        log_error "Yazi package manager 'ya' not found"
        log_info "Please ensure yazi is properly installed"
        exit 1
    fi
    
    log_info "Yazi and ya package manager are available"
}

# Install all yazi packages (plugins + themes)
install_yazi_packages() {
    log_subsection "Installing Yazi plugins and themes"
    install_yazi_plugins
    install_yazi_themes
}

# Check if yazi package is already installed
check_yazi_package_installed() {
    local package="$1"
    local type="${2:-package}"
    
    # Extract package name from the full package specification
    local package_name="${package##*:}"
    
    # Check if package is already installed
    if ya pkg list 2>/dev/null | grep -q "$package_name"; then
        log_info "$type already installed: $package_name"
        return 0  # Package is installed, continue processing
    else
        return 1  # Package not installed, skip to next
    fi
}

# Install yazi plugins
install_yazi_plugins() {
    log_subsection "Installing Yazi plugins"
    
    local plugins=(
        "yazi-rs/plugins:git"
    )
    
    for plugin in "${plugins[@]}"; do
        if check_yazi_package_installed "$plugin" "plugin"; then
            log_info "Skipping already installed plugin: $plugin"
            continue  # Plugin already installed, skip to next
        fi
        log_info "Installing plugin: $plugin" && \
        install_yazi_package "$plugin" "plugin"
    done
    
    log_success "Yazi plugins installation completed"
}

check_yazi_theme_installed() {
    local theme="$1"
    
    # Extract theme name from the full theme specification
    local theme_name="${theme##*:}"
    
    # Check if theme is already installed
    if ya pkg list 2>/dev/null | grep -q "$theme_name"; then
        log_info "Theme already installed: $theme_name"
        return 0  # Theme is installed, continue processing
    else
        return 1  # Theme not installed, skip to next
    fi
}

# Install yazi themes
install_yazi_themes() {
    log_subsection "Installing Yazi themes"
    
    local themes=(
        "yazi-rs/flavors:catppuccin-mocha"
        "yazi-rs/flavors:catppuccin-frappe"
    )
    
    for theme in "${themes[@]}"; do
        if check_yazi_theme_installed "$theme"; then
            log_info "Skipping already installed theme: $theme"
            continue  # Theme already installed, skip to next
        fi
        log_info "Installing theme: $theme" && \
        # Install the theme
        install_yazi_package "$theme" "theme"
    done
    
    log_success "Yazi themes installation completed"
}

# Install individual yazi package (plugin or theme)
install_yazi_package() {
    local package="$1"
    local type="${2:-package}"
    
    log_info "Installing $type: $package"
    
    if ya pkg add "$package" >/dev/null 2>&1; then
        log_success "$type installed: $package"
    else
        log_warning "Failed to install $type: $package (may already be installed)"
    fi
}

# Update yazi packages
update_yazi_packages() {
    log_subsection "Updating Yazi plugins and themes"
    
    if ya pkg update >/dev/null 2>&1; then
        log_success "Yazi packages updated successfully"
    else
        log_warning "Failed to update some Yazi packages"
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
