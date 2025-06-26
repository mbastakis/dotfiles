#!/bin/bash
#
# Bootstrap script for macOS dotfiles setup
#
# Author: mbastakis
# Last updated: $(date '+%Y-%m-%d')
#

set -euo pipefail
IFS=$'\n\t'

# Get script directory and source utils
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/utils.sh"

# Initialize utils
init_utils

# Configuration flags
INSTALL_HOMEBREW=true
INSTALL_CORE=true
SETUP_STOW=true
INSTALL_APPS=false
INSTALL_DEV=false
INSTALL_MAS=false
SETUP_MACOS=false
SETUP_VSCODE=false
SETUP_OBSIDIAN=false
SETUP_YAZI=false
SETUP_NPM_GLOBALS=true

# Main function
main() {
    # Parse command line arguments
    parse_bootstrap_args "$@"
    
    log_section "macOS Dotfiles Bootstrap"
    log_info "This script will set up your Mac with your preferred configuration"
    
    # Show configuration summary
    show_config_summary
    
    # Confirm installation unless auto-yes is enabled
    if [[ "$FORCE_YES" != "true" ]]; then
        if ! ask_yes_no "Do you want to proceed with the installation?" "n"; then
            log_warning "Installation cancelled"
            exit 0
        fi
    fi
    
    # Validate macOS
    validate_macos
    
    # Execute installation steps
    execute_installation
    
    log_section "Bootstrap Complete!"
    log_success "Your Mac has been configured successfully"
    log_info "You may need to restart your terminal or Mac for some changes to take effect"
}

# Parse bootstrap-specific arguments
parse_bootstrap_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -y|--yes)
                FORCE_YES=true
                shift
                ;;
            --all)
                INSTALL_APPS=true
                INSTALL_DEV=true
                INSTALL_MAS=true
                SETUP_MACOS=true
                SETUP_VSCODE=true
                SETUP_OBSIDIAN=true
                SETUP_YAZI=true
                SETUP_NPM_GLOBALS=true
                shift
                ;;
            --core)
                INSTALL_CORE=true
                shift
                ;;
            --apps)
                INSTALL_APPS=true
                shift
                ;;
            --dev)
                INSTALL_DEV=true
                shift
                ;;
            --mas)
                INSTALL_MAS=true
                shift
                ;;
            --macos)
                SETUP_MACOS=true
                shift
                ;;
            --vscode)
                SETUP_VSCODE=true
                shift
                ;;
            --obsidian)
                SETUP_OBSIDIAN=true
                shift
                ;;
            --yazi)
                SETUP_YAZI=true
                shift
                ;;
            --npm-globals)
                SETUP_NPM_GLOBALS=true
                shift
                ;;
            --no-homebrew)
                INSTALL_HOMEBREW=false
                shift
                ;;
            --no-stow)
                SETUP_STOW=false
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
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
    
    # Export variables for child scripts
    export VERBOSE DRY_RUN FORCE_YES
}

# Show configuration summary
show_config_summary() {
    log_subsection "Installation Configuration"
    echo "Homebrew:        $([ "$INSTALL_HOMEBREW" = true ] && echo "✓ Install" || echo "✗ Skip")"
    echo "Core packages:   $([ "$INSTALL_CORE" = true ] && echo "✓ Install" || echo "✗ Skip")"
    echo "GUI apps:        $([ "$INSTALL_APPS" = true ] && echo "✓ Install" || echo "✗ Skip")"
    echo "Dev tools:       $([ "$INSTALL_DEV" = true ] && echo "✓ Install" || echo "✗ Skip")"
    echo "Mac App Store:   $([ "$INSTALL_MAS" = true ] && echo "✓ Install" || echo "✗ Skip")"
    echo "macOS settings:  $([ "$SETUP_MACOS" = true ] && echo "✓ Apply" || echo "✗ Skip")"
    echo "VS Code:         $([ "$SETUP_VSCODE" = true ] && echo "✓ Setup" || echo "✗ Skip")"
    echo "Obsidian:        $([ "$SETUP_OBSIDIAN" = true ] && echo "✓ Setup" || echo "✗ Skip")"
    echo "Yazi:            $([ "$SETUP_YAZI" = true ] && echo "✓ Setup" || echo "✗ Skip")"
    echo "NPM Globals:     $([ "$SETUP_NPM_GLOBALS" = true ] && echo "✓ Install" || echo "✗ Skip")"
    echo "Stow configs:    $([ "$SETUP_STOW" = true ] && echo "✓ Link" || echo "✗ Skip")"
    echo ""
}

# Execute installation steps
execute_installation() {
    # Install Homebrew
    if [[ "$INSTALL_HOMEBREW" == "true" ]]; then
        log_section "Installing Homebrew"
        "$SCRIPT_DIR/scripts/install_brew.sh"
        
        # Install GNU Stow
        log_info "Installing GNU Stow"
        if [[ "$DRY_RUN" != "true" ]]; then
            brew install stow
        else
            log_info "[DRY RUN] Would install GNU Stow"
        fi
    fi
    
    # Setup Stow configurations
    if [[ "$SETUP_STOW" == "true" ]]; then
        setup_stow_configs
    fi
    
    # Install Homebrew packages
    install_homebrew_packages
    
    # Apply macOS settings
    if [[ "$SETUP_MACOS" == "true" ]]; then
        setup_macos_settings
    fi
    
    # Setup applications
    if [[ "$SETUP_VSCODE" == "true" ]]; then
        setup_vscode_config
    fi
    
    if [[ "$SETUP_OBSIDIAN" == "true" ]]; then
        setup_obsidian_config
    fi
    
    # Setup Yazi file manager
    if [[ "$SETUP_YAZI" == "true" ]]; then
        setup_yazi_config
    fi
    
    # Install NPM global tools
    if [[ "$SETUP_NPM_GLOBALS" == "true" ]]; then
        setup_npm_globals
    fi
}

# Setup Stow configurations
setup_stow_configs() {
    log_section "Linking Configuration Files"
    
    if ! command_exists stow; then
        log_error "GNU Stow not installed, cannot link configurations"
        return 1
    fi
    
    "$SCRIPT_DIR/bin/manage_stow" stow --all
}

# Install Homebrew packages
install_homebrew_packages() {
    local categories=()
    
    # Build categories list based on flags
    if [[ "$INSTALL_CORE" == "true" ]]; then
        categories+=("core")
    fi
    
    if [[ "$INSTALL_APPS" == "true" ]]; then
        categories+=("apps")
    fi
    
    if [[ "$INSTALL_DEV" == "true" ]]; then
        categories+=("dev")
    fi
    
    if [[ "$INSTALL_MAS" == "true" ]]; then
        categories+=("mas")
    fi
    
    # Install packages if any categories selected
    if [ ${#categories[@]} -gt 0 ]; then
        log_section "Installing Homebrew Packages"
        
        local category_list
        category_list=$(IFS=','; echo "${categories[*]}")
        
        "$SCRIPT_DIR/bin/manage_brew" install -c "$category_list" --update-first
    fi
}

# Setup macOS settings
setup_macos_settings() {
    log_section "Configuring macOS Settings"
    "$SCRIPT_DIR/scripts/mac_settings.sh"
}

# Setup VS Code configuration
setup_vscode_config() {
    log_section "Setting up VS Code Configuration"
    
    local extensions_file="$SCRIPT_DIR/vscode/extensions.txt"
    local should_install_extensions=false
    
    # Always sync configuration (settings, keybindings, TUI Manager)
    "$SCRIPT_DIR/bin/setup_vscode" sync
    
    # Determine if we should install extensions
    if command_exists code; then
        # Check if extensions.txt is newer than last installation
        # or if this is first time setup (no extensions installed)
        local installed_extensions
        installed_extensions=$(code --list-extensions | wc -l | tr -d ' ')
        
        if [ "$installed_extensions" -eq 0 ]; then
            log_info "No extensions currently installed, will install from dotfiles"
            should_install_extensions=true
        elif [ -f "$extensions_file" ]; then
            # Check if we have significantly fewer extensions than listed
            local expected_extensions
            expected_extensions=$(grep -v "^#" "$extensions_file" | grep -v "^$" | wc -l | tr -d ' ')
            
            # Install if we have less than 80% of expected extensions
            local threshold=$((expected_extensions * 80 / 100))
            if [ "$installed_extensions" -lt "$threshold" ]; then
                log_info "Only $installed_extensions of $expected_extensions extensions installed, updating..."
                should_install_extensions=true
            else
                log_info "Extensions appear up-to-date ($installed_extensions installed), skipping installation"
            fi
        fi
        
        if [ "$should_install_extensions" = true ]; then
            "$SCRIPT_DIR/bin/setup_vscode" extensions install
        fi
    else
        log_warning "VS Code CLI not available, skipping extensions installation"
    fi
}

# Setup Obsidian configuration
setup_obsidian_config() {
    log_section "Setting up Obsidian Configuration"
    "$SCRIPT_DIR/scripts/setup_obsidian.sh"
}

# Setup Yazi file manager
setup_yazi_config() {
    log_section "Setting up Yazi File Manager"
    "$SCRIPT_DIR/scripts/setup_yazi.sh" setup
}

# Setup NPM global tools
setup_npm_globals() {
    log_section "Installing NPM Global Tools"
    "$SCRIPT_DIR/scripts/setup_npm_globals.sh" install
}

# Help function
show_help() {
    cat << EOF
macOS Dotfiles Bootstrap Script

Usage: $0 [OPTIONS]

Options:
    -y, --yes           Answer yes to all prompts (non-interactive mode)
    --all               Install everything (apps, dev tools, MAS, macOS settings, etc.)
    --core              Install core Homebrew packages (default: true)
    --apps              Install GUI applications
    --dev               Install development tools
    --mas               Install Mac App Store applications
    --macos             Apply macOS system settings
    --vscode            Setup VS Code configuration and extensions
    --obsidian          Setup Obsidian vault configuration
    --yazi              Setup Yazi file manager plugins and themes
    --npm-globals       Install global NPM tools (Claude Code, etc.)
    --no-homebrew       Skip Homebrew installation
    --no-stow           Skip stow configuration linking
    -v, --verbose       Enable verbose output
    --dry-run           Show what would be done without executing
    -h, --help          Show this help message

Examples:
    $0                          # Interactive installation with core packages
    $0 -y --all                 # Non-interactive full installation
    $0 --dev --vscode          # Install only dev tools and VS Code setup
    $0 --apps --mas --macos    # Install GUI apps, MAS apps, and apply macOS settings
    $0 --yazi --npm-globals    # Setup Yazi and install global NPM tools
    $0 --dry-run --all         # Preview full installation without executing

Component Details:
    core      - Essential CLI tools and utilities
    apps      - GUI applications (browsers, productivity tools, etc.)
    dev       - Development tools (IDEs, languages, databases, etc.)
    mas       - Mac App Store applications
    macos     - System preferences and settings
    vscode    - VS Code settings, keybindings, and extensions
    obsidian  - Obsidian vault configuration syncing
    yazi      - Yazi file manager plugins and themes setup
    npm-glob  - Global NPM tools (Claude Code, ni, ncu, etc.)
    stow      - Symlink dotfiles configurations to home directory
EOF
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
