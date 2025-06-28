#!/usr/bin/env bash
#
# NPM Global Tools Setup Script
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

# Global NPM packages to install
declare -A NPM_PACKAGES=(
    ["@anthropic-ai/claude-code"]="Claude Code CLI - AI-powered coding assistant"
    ["@mariozechner/snap-happy"]="Cross-platform screenshot tool for AI assistants"
    ["@google/gemini-cli"]="Gemini CLI - Google Gemini command line interface"
    ["@vscode/vsce"]="VSCE - Visual Studio Code Extension Manager"
    ["@antfu/ni"]="Package manager agnostic commands"
    ["npm-check-updates"]="Update package.json dependencies to latest versions"
    ["http-server"]="Simple HTTP server for local development"
    ["json-server"]="Full fake REST API with zero coding"
)

# Main function
main() {
    local action=""
    local specific_package=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            install|setup)
                action="install"
                shift
                ;;
            update)
                action="update"
                shift
                ;;
            list)
                action="list"
                shift
                ;;
            remove|uninstall)
                action="remove"
                shift
                ;;
            --package)
                specific_package="$2"
                shift 2
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
        action="install"
    fi
    
    log_section "NPM Global Tools Setup"
    
    # Validate Node.js and npm
    check_node_npm_installed
    
    # Execute action
    case "$action" in
        "install")
            if [ -n "$specific_package" ]; then
                install_specific_package "$specific_package"
            else
                install_all_packages
            fi
            ;;
        "update")
            if [ -n "$specific_package" ]; then
                update_specific_package "$specific_package"
            else
                update_all_packages
            fi
            ;;
        "list")
            list_packages
            ;;
        "remove")
            if [ -n "$specific_package" ]; then
                remove_specific_package "$specific_package"
            else
                log_error "Package name required for removal. Use --package <package-name>"
                exit 1
            fi
            ;;
        *)
            log_error "Unknown action: $action"
            exit 1
            ;;
    esac
    
    log_section "NPM Global Tools Setup Complete"
}

# Check if Node.js and npm are installed
check_node_npm_installed() {
    if ! command_exists node; then
        log_error "Node.js not found. Please install Node.js first."
        log_info "You can install Node.js via Homebrew: brew install node"
        exit 1
    fi
    
    if ! command_exists npm; then
        log_error "npm not found. Please install npm first."
        exit 1
    fi
    
    log_info "Node.js version: $(node --version)"
    log_info "npm version: $(npm --version)"
}

# Install all packages
install_all_packages() {
    log_subsection "Installing NPM global packages"
    
    for package in "${!NPM_PACKAGES[@]}"; do
        install_npm_package "$package" "${NPM_PACKAGES[$package]}"
    done
    
    log_success "All NPM global packages installation completed"
}

# Install specific package
install_specific_package() {
    local package="$1"
    local description="${NPM_PACKAGES[$package]:-$package}"
    
    log_subsection "Installing specific NPM package"
    install_npm_package "$package" "$description"
}

# Install individual npm package
install_npm_package() {
    local package="$1"
    local description="$2"
    
    log_info "Installing: $package"
    log_debug "Description: $description"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        if npm list -g "$package" >/dev/null 2>&1; then
            log_info "$package is already installed globally"
        else
            if npm install -g "$package"; then
                log_success "Installed: $package"
            else
                log_error "Failed to install: $package"
                return 1
            fi
        fi
    else
        log_info "[DRY RUN] Would install: $package"
    fi
}

# Update all packages
update_all_packages() {
    log_subsection "Updating NPM global packages"
    
    for package in "${!NPM_PACKAGES[@]}"; do
        update_npm_package "$package"
    done
    
    log_success "All NPM global packages update completed"
}

# Update specific package
update_specific_package() {
    local package="$1"
    
    log_subsection "Updating specific NPM package"
    update_npm_package "$package"
}

# Update individual npm package
update_npm_package() {
    local package="$1"
    
    log_info "Updating: $package"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        if npm list -g "$package" >/dev/null 2>&1; then
            if npm update -g "$package"; then
                log_success "Updated: $package"
            else
                log_warning "Failed to update: $package"
            fi
        else
            log_warning "$package is not installed globally, installing instead..."
            install_npm_package "$package" "${NPM_PACKAGES[$package]:-$package}"
        fi
    else
        log_info "[DRY RUN] Would update: $package"
    fi
}

# Remove specific package
remove_specific_package() {
    local package="$1"
    
    log_subsection "Removing NPM package: $package"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        if npm list -g "$package" >/dev/null 2>&1; then
            if npm uninstall -g "$package"; then
                log_success "Removed: $package"
            else
                log_error "Failed to remove: $package"
                return 1
            fi
        else
            log_warning "$package is not installed globally"
        fi
    else
        log_info "[DRY RUN] Would remove: $package"
    fi
}

# List packages
list_packages() {
    log_subsection "NPM Global Packages Status"
    
    echo "Managed packages:"
    for package in "${!NPM_PACKAGES[@]}"; do
        local status="NOT INSTALLED"
        local version=""
        
        if npm list -g "$package" >/dev/null 2>&1; then
            version=$(npm list -g "$package" --depth=0 2>/dev/null | grep "$package" | cut -d'@' -f2 || echo "unknown")
            status="INSTALLED (v$version)"
        fi
        
        printf "  %-30s %s\n" "$package" "$status"
        printf "  %-30s %s\n" "" "${NPM_PACKAGES[$package]}"
        echo
    done
    
    log_subsection "All Currently Installed Global Packages"
    npm list -g --depth=0
}

# Help function
show_help() {
    cat << EOF
NPM Global Tools Setup Script

Usage: $0 [ACTION] [OPTIONS]

Actions:
    install, setup      Install all managed NPM global packages (default)
    update             Update all managed NPM global packages
    list               List status of managed packages and all global packages
    remove, uninstall  Remove a specific package (requires --package)

Options:
    --package NAME     Specify a specific package for install/update/remove actions
    -v, --verbose      Enable verbose output
    -y, --yes         Answer yes to all prompts
    --dry-run         Show what would be done without executing
    -h, --help        Show this help message

Examples:
    $0                                    # Install all managed packages
    $0 update                            # Update all managed packages
    $0 install --package claude-code     # Install only Claude Code
    $0 update --package claude-code      # Update only Claude Code
    $0 remove --package claude-code      # Remove Claude Code
    $0 list                              # Show package status
    $0 --dry-run                         # Preview operations

Managed Global Packages:
EOF

    for package in "${!NPM_PACKAGES[@]}"; do
        printf "    %-30s %s\n" "$package" "${NPM_PACKAGES[$package]}"
    done
    
    cat << EOF

Notes:
    - Requires Node.js and npm to be installed
    - Install Node.js via Homebrew: brew install node
    - Packages are installed globally and available system-wide
EOF
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
