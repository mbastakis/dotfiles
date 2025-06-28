#!/bin/bash

# List VSCode Extensions Script
# This script manages VSCode extension listing and synchronization

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VSCODE_EXT_FILE="$DOTFILES_ROOT/vscode_extensions/extensions.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if VSCode is installed
check_vscode() {
    if ! command -v code &> /dev/null; then
        log_error "VSCode CLI 'code' command not found. Please install VSCode and ensure it's in your PATH."
        exit 1
    fi
    log_info "VSCode CLI found"
}

# List installed extensions
list_extensions() {
    log_info "Listing installed VSCode extensions..."
    code --list-extensions --show-versions
}

# Export extensions to file
export_extensions() {
    log_info "Exporting installed extensions to $VSCODE_EXT_FILE"
    
    # Create directory if it doesn't exist
    mkdir -p "$(dirname "$VSCODE_EXT_FILE")"
    
    # Export extensions
    code --list-extensions > "$VSCODE_EXT_FILE"
    
    log_success "Extensions exported to $VSCODE_EXT_FILE"
    log_info "$(wc -l < "$VSCODE_EXT_FILE") extensions exported"
}

# Install extensions from file
install_extensions() {
    if [[ ! -f "$VSCODE_EXT_FILE" ]]; then
        log_error "Extensions file not found: $VSCODE_EXT_FILE"
        exit 1
    fi
    
    log_info "Installing extensions from $VSCODE_EXT_FILE"
    
    local count=0
    while IFS= read -r extension; do
        if [[ -n "$extension" ]] && [[ ! "$extension" =~ ^[[:space:]]*# ]]; then
            log_info "Installing: $extension"
            if code --install-extension "$extension"; then
                ((count++))
            else
                log_warning "Failed to install: $extension"
            fi
        fi
    done < "$VSCODE_EXT_FILE"
    
    log_success "Installed $count extensions"
}

# Show help
show_help() {
    cat << EOF
VSCode Extensions Management Script

Usage: $0 [COMMAND]

Commands:
    list        List currently installed extensions
    export      Export installed extensions to extensions.txt
    install     Install extensions from extensions.txt
    sync        Export current extensions and show diff with file
    help        Show this help message

Examples:
    $0 list                # List all installed extensions
    $0 export              # Save current extensions to file
    $0 install             # Install extensions from file
    $0 sync                # Show differences between installed and file

EOF
}

# Sync extensions (show differences)
sync_extensions() {
    if [[ ! -f "$VSCODE_EXT_FILE" ]]; then
        log_warning "Extensions file not found: $VSCODE_EXT_FILE"
        log_info "Creating file with current extensions..."
        export_extensions
        return
    fi
    
    log_info "Comparing installed extensions with $VSCODE_EXT_FILE"
    
    # Get current extensions
    local temp_file
    temp_file=$(mktemp)
    code --list-extensions > "$temp_file"
    
    # Compare files
    if diff -q "$VSCODE_EXT_FILE" "$temp_file" > /dev/null; then
        log_success "Extensions are in sync"
    else
        log_info "Extensions differ:"
        echo
        echo "--- Extensions in file ---"
        cat "$VSCODE_EXT_FILE"
        echo
        echo "--- Currently installed ---"
        cat "$temp_file"
        echo
        echo "--- Diff ---"
        diff "$VSCODE_EXT_FILE" "$temp_file" || true
    fi
    
    rm "$temp_file"
}

# Main function
main() {
    local command="${1:-help}"
    
    case "$command" in
        list)
            check_vscode
            list_extensions
            ;;
        export)
            check_vscode
            export_extensions
            ;;
        install)
            check_vscode
            install_extensions
            ;;
        sync)
            check_vscode
            sync_extensions
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"