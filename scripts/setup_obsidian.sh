#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# Include utility functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit
source "$SCRIPT_DIR/utils.sh"

# Default vault path - can be overridden
DEFAULT_VAULT_PATH="$HOME/Documents"

setup_obsidian_vault() {
    local vault_path="$1"
    local vault_name="$2"
    local full_vault_path="$vault_path/$vault_name"
    local obsidian_config_source="$DOTFILES_PATH/obsidian/.obsidian"
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
    log_section "Obsidian Configuration Setup"
    
    # Ask for vault location
    read -p "Enter the path where your Obsidian vaults are located [$DEFAULT_VAULT_PATH]: " vault_path
    vault_path="${vault_path:-$DEFAULT_VAULT_PATH}"
    
    # Expand tilde to home directory
    vault_path="${vault_path/#\~/$HOME}"
    
    if [ ! -d "$vault_path" ]; then
        log_error "Path '$vault_path' does not exist"
        exit 1
    fi
    
    # List potential vaults
    if ! list_potential_vaults "$vault_path"; then
        log_info "You can manually specify a vault name"
    fi
    
    # Ask for vault name
    read -p "Enter the name of your Obsidian vault: " vault_name
    
    if [ -z "$vault_name" ]; then
        log_error "Vault name cannot be empty"
        exit 1
    fi
    
    # Setup the vault
    setup_obsidian_vault "$vault_path" "$vault_name"
    
    # Ask if user wants to setup additional vaults
    while true; do
        read -p "Do you want to setup another vault? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter the name of another Obsidian vault: " vault_name
            if [ -n "$vault_name" ]; then
                setup_obsidian_vault "$vault_path" "$vault_name"
            fi
        else
            break
        fi
    done
    
    log_section "Obsidian Setup Complete"
    log_info "Your Obsidian configuration is now synced with your dotfiles"
    log_info "Changes made in Obsidian will be reflected in your dotfiles repository"
    log_info "Don't forget to commit and push your changes!"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
