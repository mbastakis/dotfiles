#!/bin/bash

# install_vscode_extensions.sh
# Installs VSCode extensions from .vsix files in data/vscode_extensions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EXTENSIONS_DATA_DIR="$DOTFILES_ROOT/vscode_extensions"

# Source the shared utilities
source "$SCRIPT_DIR/utils.sh" 2>/dev/null || {
    # Fallback logging if utils.sh is not available
    log_info() { echo "[INFO] $1"; }
    log_error() { echo "[ERROR] $1" >&2; }
    log_success() { echo "[SUCCESS] $1"; }
    log_warning() { echo "[WARNING] $1" >&2; }
}

check_vscode() {
    if ! command -v code >/dev/null 2>&1; then
        log_error "VSCode 'code' command not found. Please install VSCode and ensure 'code' is in your PATH."
        exit 1
    fi
    log_info "VSCode found: $(which code)"
}

package_extension() {
    local extension_dir="$1"
    local extension_name=""
    extension_name="$(basename "$extension_dir")"
    if [[ ! -d "$extension_dir" ]]; then
        log_error "Extension directory not found: $extension_dir"
        return 1
    fi

    log_info "Packaging extension: $extension_name"
    
    cd "$extension_dir"
    
    # Check if vsce is available
    if ! command -v vsce >/dev/null 2>&1; then
        log_error "vsce (Visual Studio Code Extension manager) not found."
        log_error "Install it with: npm install -g vsce"
        exit 1
    fi
    
    # Package the extension
    vsce package --allow-missing-repository --out "$extension_name.vsix"
    
    if [[ ! -f "$extension_name.vsix" ]]; then
        log_error "Failed to create $extension_name.vsix"
        return 1
    fi
    
    log_info "Successfully packaged $extension_name.vsix"
}

install_extension() {
    local vsix_file="$1"
    local extension_name=""
    extension_name="$(basename "$vsix_file" .vsix)"
    if [[ ! -f "$vsix_file" ]]; then
        log_error "VSIX file not found: $vsix_file"
        return 1
    fi

    log_info "Installing extension: $extension_name"
    
    # Try to install the extension
    local install_output
    install_output=$(code --user-data-dir ~/.vscode --install-extension "$vsix_file" 2>&1)
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_info "Successfully installed $extension_name"
        return 0
    else
        # Check if the error is about restarting VS Code
        if echo "$install_output" | grep -q "Please restart VS Code"; then
            log_info "Extension $extension_name requires VS Code restart - this is normal for reinstallation"
            log_info "The extension will be active after VS Code is restarted"
            return 0  # Treat this as success since it's expected behavior
        else
            log_error "Failed to install $extension_name"
            log_error "Output: $install_output"
            return 1
        fi
    fi
}

main() {
    log_info "Starting VSCode Extensions Installation"
    log_info "Extensions data directory: $EXTENSIONS_DATA_DIR"
    
    check_vscode
    
    if [[ ! -d "$EXTENSIONS_DATA_DIR" ]]; then
        log_error "Extensions data directory not found: $EXTENSIONS_DATA_DIR"
        exit 1
    fi
    
    local installed_count=0
    local failed_count=0
    
    # Process each extension directory
    for extension_dir in "$EXTENSIONS_DATA_DIR"/*; do
        if [[ ! -d "$extension_dir" ]]; then
            continue
        fi
        
        local extension_name=""
        extension_name="$(basename "$extension_dir")"
        log_info "Processing extension directory: $extension_name"
        
        # Check if package.json exists
        if [[ ! -f "$extension_dir/package.json" ]]; then
            log_error "No package.json found in $extension_dir, skipping"
            ((failed_count++))
            continue
        fi
        
        # Check if a .vsix file already exists
        local vsix_file=""
        for vsix in "$extension_dir"/*.vsix; do
            if [[ -f "$vsix" ]]; then
                vsix_file="$vsix"
                log_info "Found existing VSIX file: $vsix_file"
                break
            fi
        done
        
        # If no .vsix file exists, package the extension
        if [[ -z "$vsix_file" ]]; then
            if package_extension "$extension_dir"; then
                vsix_file="$extension_dir/$extension_name.vsix"
                log_info "VSIX file created: $vsix_file"
            else
                ((failed_count++))
                continue
            fi
        fi
        
        # Install the extension
        if install_extension "$vsix_file"; then
            ((installed_count++))
            # Don't delete pre-existing .vsix files, only clean up ones we created
            if [[ "$vsix_file" == "$extension_dir/$extension_name.vsix" ]] && [[ ! -f "$extension_dir/tui-manager-1.0.0.vsix" ]]; then
                rm -f "$vsix_file"
                log_info "Cleaned up $vsix_file"
            fi
        else
            ((failed_count++))
        fi
    done

    log_info "VSCode Extensions Installation complete!"
    log_info "Successfully installed: $installed_count extensions"
    
    if [[ $failed_count -gt 0 ]]; then
        log_error "Failed to install: $failed_count extensions"
        exit 1
    fi

    log_info "All extensions processed"
    exit 0
}

main "$@"
