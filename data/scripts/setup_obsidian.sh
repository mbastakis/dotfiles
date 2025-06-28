#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# Include utility functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_PATH="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/utils.sh"

# Initialize utils
init_utils

# Default vault path - can be overridden
DEFAULT_VAULT_PATH="$HOME/Documents"

setup_obsidian_vault() {
    local vault_path="$1"
    local vault_name="$2"
    local full_vault_path="$vault_path/$vault_name"
    local obsidian_config_source="$DOTFILES_ROOT/obsidian/.obsidian"
    local obsidian_config_target="$full_vault_path/.obsidian"
    
    if [ ! -d "$full_vault_path" ]; then
        log_error "Vault directory '$full_vault_path' does not exist"
        return 1
    fi
    
    if [ ! -d "$obsidian_config_source" ]; then
        log_error "Obsidian configuration source '$obsidian_config_source' does not exist"
        return 1
    fi
    
    # Backup existing .obsidian if it exists and is not a symlink
    if [ -d "$obsidian_config_target" ] && [ ! -L "$obsidian_config_target" ]; then
        log_info "Backing up existing .obsidian configuration"
        mv "$obsidian_config_target" "${obsidian_config_target}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Remove existing symlink if it exists
    if [ -L "$obsidian_config_target" ]; then
        log_info "Removing existing symlink"
        rm "$obsidian_config_target"
    fi
    
    # Create the symlink
    log_info "Creating symlink from '$obsidian_config_source' to '$obsidian_config_target'"
    ln -sf "$obsidian_config_source" "$obsidian_config_target"
    
    log_info  "Obsidian configuration linked successfully for vault: $vault_name"
}

list_potential_vaults() {
    local search_path="$1"
    log_info "Searching for Obsidian vaults in: $search_path"
    
    if [ ! -d "$search_path" ]; then
        log_warning "Directory '$search_path' does not exist"
        return 1
    fi
    
    local vaults=()
    while IFS= read -r -d '' dir; do
        local dirname
        dirname=$(basename "$dir")
        # Skip hidden directories and common non-vault directories
        if [[ ! "$dirname" =~ ^\. ]] && [[ ! "$dirname" =~ ^(Applications|Desktop|Downloads|Library|Movies|Music|Pictures|Public)$ ]]; then
            vaults+=("$dirname")
        fi
    done < <(find "$search_path" -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null)
    
    if [ ${#vaults[@]} -eq 0 ]; then
        log_warning "No potential vault directories found in $search_path"
        return 1
    fi
    
    echo "Found potential vaults:"
    for i in "${!vaults[@]}"; do
        echo "  $((i+1)). ${vaults[$i]}"
    done
    
    return 0
}

# Main script logic
main() {
    local vault_path="$DEFAULT_VAULT_PATH"
    local vault_names=()
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--path)
                vault_path="$2"
                shift 2
                ;;
            -v|--vault)
                vault_names+=("$2")
                shift 2
                ;;
            --verbose)
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
    
    log_section "Obsidian Configuration Setup"
    
    # Interactive mode if no vaults specified
    if [ ${#vault_names[@]} -eq 0 ]; then
        setup_interactive "$vault_path"
    else
        setup_automated "$vault_path" "${vault_names[@]}"
    fi
    
    log_section "Obsidian Setup Complete"
    log_success "Your Obsidian configuration is now synced with your dotfiles"
    log_info "Changes made in Obsidian will be reflected in your dotfiles repository"
    log_info "Don't forget to commit and push your changes!"
}

# Interactive setup mode
setup_interactive() {
    local vault_path="$1"
    
    # Ask for vault location if not in force mode
    if [[ "$FORCE_YES" != "true" ]]; then
        read -p "Enter the path where your Obsidian vaults are located [$vault_path]: " input_path
        vault_path="${input_path:-$vault_path}"
    fi
    
    # Expand tilde to home directory
    vault_path="${vault_path/#\~/$HOME}"
    
    if [ ! -d "$vault_path" ]; then
        die "Path '$vault_path' does not exist"
    fi
    
    # List potential vaults
    if ! list_potential_vaults "$vault_path"; then
        log_info "You can manually specify a vault name"
    fi
    
    # Ask for vault name
    local vault_name
    if [[ "$FORCE_YES" == "true" ]]; then
        log_warning "Force mode enabled but no vault specified, skipping setup"
        return 0
    fi
    
    read -p "Enter the name of your Obsidian vault: " vault_name
    
    if [ -z "$vault_name" ]; then
        die "Vault name cannot be empty"
    fi
    
    # Setup the vault
    setup_obsidian_vault "$vault_path" "$vault_name"
    
    # Ask if user wants to setup additional vaults
    while [[ "$FORCE_YES" != "true" ]]; do
        if ask_yes_no "Do you want to setup another vault?" "n"; then
            read -p "Enter the name of another Obsidian vault: " vault_name
            if [ -n "$vault_name" ]; then
                setup_obsidian_vault "$vault_path" "$vault_name"
            fi
        else
            break
        fi
    done
}

# Automated setup mode
setup_automated() {
    local vault_path="$1"
    shift
    local vault_names=("$@")
    
    # Expand tilde to home directory
    vault_path="${vault_path/#\~/$HOME}"
    
    if [ ! -d "$vault_path" ]; then
        die "Path '$vault_path' does not exist"
    fi
    
    # Setup each specified vault
    for vault_name in "${vault_names[@]}"; do
        setup_obsidian_vault "$vault_path" "$vault_name"
    done
}

# Help function
show_help() {
    cat << EOF
Obsidian Configuration Setup Script

Usage: $0 [OPTIONS]

Options:
    -p, --path PATH     Path where Obsidian vaults are located (default: $DEFAULT_VAULT_PATH)
    -v, --vault NAME    Vault name to setup (can be used multiple times)
    --verbose           Enable verbose output
    -y, --yes          Answer yes to all prompts
    --dry-run          Show what would be done without executing
    -h, --help         Show this help message

Examples:
    $0                                    # Interactive setup
    $0 -p ~/Documents -v "My Vault"      # Setup specific vault
    $0 -v "Vault1" -v "Vault2"          # Setup multiple vaults
    $0 --dry-run                         # Preview setup operations
    $0 -y -p ~/Obsidian -v "Work"       # Non-interactive setup

This script creates symlinks from your dotfiles Obsidian configuration
to your vault directories, allowing settings to be version controlled.
EOF
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
