#!/bin/bash

# Build VSCode Extensions Script
# This script manages VSCode extension building and installation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VSCODE_EXT_DIR="$DOTFILES_ROOT/vscode_extensions"

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

# Build extension if directory exists
build_extension() {
    local ext_dir="$1"
    local ext_name="$(basename "$ext_dir")"
    
    if [[ ! -d "$ext_dir" ]]; then
        log_warning "Extension directory not found: $ext_dir"
        return 1
    fi
    
    log_info "Building extension: $ext_name"
    
    cd "$ext_dir"
    
    # Check if package.json exists
    if [[ ! -f "package.json" ]]; then
        log_error "No package.json found in $ext_dir"
        return 1
    fi
    
    # Install dependencies if needed
    if [[ -f "package-lock.json" ]] && [[ ! -d "node_modules" ]]; then
        log_info "Installing dependencies for $ext_name"
        npm install
    fi
    
    # Check if vsce is available
    if ! command -v vsce &> /dev/null; then
        log_warning "vsce not found, installing globally"
        npm install -g @vscode/vsce
    fi
    
    # Build the extension
    log_info "Packaging extension $ext_name"
    vsce package --out "$VSCODE_EXT_DIR/"
    
    log_success "Extension $ext_name built successfully"
}

# Main function
main() {
    log_info "Building VSCode extensions..."
    
    check_vscode
    
    # Create output directory
    mkdir -p "$VSCODE_EXT_DIR"
    
    # Build all extensions in the extensions directory
    if [[ -d "$VSCODE_EXT_DIR/extensions" ]]; then
        for ext_dir in "$VSCODE_EXT_DIR/extensions"/*; do
            if [[ -d "$ext_dir" ]]; then
                build_extension "$ext_dir"
            fi
        done
    else
        log_warning "No extensions directory found at $VSCODE_EXT_DIR/extensions"
        log_info "Create extension projects in $VSCODE_EXT_DIR/extensions/ to use this script"
    fi
    
    log_success "VSCode extension building completed"
}

# Run main function
main "$@"