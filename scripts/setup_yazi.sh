#!/usr/bin/env bash
#
# Yazi file manager setup script
#
# Author: mbastakis
# Last updated: $(date '+%Y-%m-%d')
#

set -euo pipefail
IFS=$'\n\t'

# Get script directory and source utils
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_ROOT="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/utils.sh"

# Initialize utils
init_utils

# Yazi configuration paths
YAZI_CONFIG_DIR="$HOME/.config/yazi"
DOTFILES_YAZI_DIR="$DOTFILES_ROOT/config/.config/yazi"

# Main function
main() {
    local action=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            setup|install)
                action="setup"
                shift
                ;;
            update)
                action="update"
                shift
                ;;
            plugins)
                action="plugins"
                shift
                ;;
            themes)
                action="themes"
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -y|--yes)
                FORCE_YES=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Default action
    if [ -z "$action" ]; then
        action="setup"
    fi
    
    log_section "Yazi File Manager Setup"
    
    # Validate yazi is available
    check_yazi_installed
    
    # Execute action
    case "$action" in
        "setup")
            setup_yazi_complete
            ;;
        "update")
            update_yazi_plugins
            ;;
        "plugins")
            install_yazi_plugins
            ;;
        "themes")
            install_yazi_themes
            ;;
        *)
            log_error "Unknown action: $action"
            exit 1
            ;;
    esac
    
    log_section "Yazi Setup Complete"
}

# Check if yazi is installed
check_yazi_installed() {
    if ! command_exists yazi; then
        log_warning "Yazi not found. Installing via Homebrew..."
        if [[ "$DRY_RUN" != "true" ]]; then
            if ! command_exists brew; then
                die "Homebrew not installed. Please install Homebrew first."
            fi
            brew install yazi
            log_success "Yazi installed successfully"
        else
            log_info "[DRY RUN] Would install yazi via Homebrew"
        fi
    else
        log_info "Yazi is already installed"
    fi
    
    if ! command_exists ya; then
        log_error "Yazi package manager 'ya' not found after installation"
        return 1
    fi
}

# Complete yazi setup
setup_yazi_complete() {
    log_subsection "Setting up Yazi file manager"
    
    # Install plugins and themes
    install_yazi_plugins
    install_yazi_themes
    
    log_success "Yazi setup completed"
    log_info "Configuration files are managed via stow from: $DOTFILES_YAZI_DIR"
}

# Install yazi plugins
install_yazi_plugins() {
    log_subsection "Installing Yazi plugins"
    
    local plugins=(
        "yazi-rs/plugins:git"
    )
    
    for plugin in "${plugins[@]}"; do
        install_yazi_package "$plugin" "plugin"
    done
    
    log_success "Yazi plugins installation completed"
}

# Install yazi themes
install_yazi_themes() {
    log_subsection "Installing Yazi themes"
    
    local themes=(
        "yazi-rs/flavors:catppuccin-mocha"
        "yazi-rs/flavors:catppuccin-frappe"
    )
    
    for theme in "${themes[@]}"; do
        install_yazi_package "$theme" "theme"
    done
    
    log_success "Yazi themes installation completed"
}

# Install individual yazi package (plugin or theme)
install_yazi_package() {
    local package="$1"
    local type="${2:-package}"
    
    log_info "Installing $type: $package"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        if ya pkg add "$package"; then
            log_success "$type installed: $package"
        else
            log_warning "Failed to install $type: $package (may already be installed)"
        fi
    else
        log_info "[DRY RUN] Would install $type: $package"
    fi
}

# Update yazi plugins
update_yazi_plugins() {
    log_subsection "Updating Yazi plugins and themes"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        if ya pkg update; then
            log_success "Yazi packages updated successfully"
        else
            log_warning "Failed to update some Yazi packages"
        fi
    else
        log_info "[DRY RUN] Would update yazi packages"
    fi
}

# Help function
show_help() {
    cat << EOF
Yazi File Manager Setup Script

Usage: $0 [ACTION] [OPTIONS]

Actions:
    setup, install       Complete yazi setup (plugins + themes) (default)
    update              Update all installed plugins and themes
    plugins             Install only plugins
    themes              Install only themes

Options:
    -v, --verbose       Enable verbose output
    -y, --yes          Answer yes to all prompts
    --dry-run          Show what would be done without executing
    -h, --help         Show this help message

Examples:
    $0                      # Complete setup
    $0 update               # Update all packages
    $0 plugins              # Install only plugins
    $0 themes               # Install only themes
    $0 --dry-run            # Preview operations

Installed Plugins:
    - yazi-rs/plugins:git   # Git integration plugin

Installed Themes:
    - yazi-rs/flavors:catppuccin-mocha   # Catppuccin Mocha theme
    - yazi-rs/flavors:catppuccin-frappe  # Catppuccin Frappe theme

Configuration:
    Yazi configuration files are managed via stow from: $DOTFILES_YAZI_DIR
    Run 'stow config' from the dotfiles root to link configuration files.
EOF
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi