#!/bin/bash

# Enhanced utility functions for dotfiles management
# Author: mbastakis
# Last updated: $(date '+%Y-%m-%d')

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global variables
DOTFILES_ROOT="${DOTFILES_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
VERBOSE=${VERBOSE:-false}
DRY_RUN=${DRY_RUN:-false}
FORCE_YES=${FORCE_YES:-false}

# Logging functions
log_info() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS]${NC} $1"
}

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')] [DEBUG]${NC} $1"
    fi
}

log_section() {
    echo -e "\n${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] [SECTION] $1 ${NC}"
    echo -e "${BLUE}========================================${NC}"
}

log_subsection() {
    echo -e "\n${PURPLE}[$(date '+%Y-%m-%d %H:%M:%S')] [SUBSECTION] $1 ${NC}"
    echo -e "${PURPLE}----------------------------------------${NC}"
}

# Utility functions
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

ensure_dir() {
    if [ ! -d "$1" ]; then
        log_info "Creating directory: $1"
        if [[ "$DRY_RUN" != "true" ]]; then
            mkdir -p "$1"
        fi
    fi
}


check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        log_info "Some operations require sudo access"
        if [[ "$DRY_RUN" != "true" ]]; then
            sudo -v
            # Keep sudo alive
            while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &
        fi
    fi
}

# User interaction functions
ask_yes_no() {
    local question="$1"
    local default="${2:-n}"
    
    if [[ "$FORCE_YES" == "true" ]]; then
        log_debug "Auto-answering yes to: $question"
        return 0
    fi
    
    local prompt
    if [[ "$default" == "y" ]]; then
        prompt="$question (Y/n): "
    else
        prompt="$question (y/N): "
    fi
    
    while true; do
        read -p "$prompt" -n 1 -r
        echo
        case $REPLY in
            [Yy]) return 0 ;;
            [Nn]) return 1 ;;
            "") 
                if [[ "$default" == "y" ]]; then
                    return 0
                else
                    return 1
                fi
                ;;
            *) echo "Please answer yes or no." ;;
        esac
    done
}

# Homebrew functions
install_homebrew() {
    if command_exists brew; then
        log_info "Homebrew is already installed"
        return 0
    fi
    
    log_info "Installing Homebrew"
    if [[ "$DRY_RUN" != "true" ]]; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        
        brew update
        log_success "Homebrew installed successfully"
    else
        log_info "[DRY RUN] Would install Homebrew"
    fi
}

install_brew_bundle() {
    local brewfile="$1"
    local description="${2:-packages}"
    
    if [ ! -f "$brewfile" ]; then
        log_error "Brewfile not found: $brewfile"
        return 1
    fi
    
    log_info "Installing $description from $brewfile"
    if [[ "$DRY_RUN" != "true" ]]; then
        brew bundle --file="$brewfile"
        log_success "$description installed successfully"
    else
        log_info "[DRY RUN] Would install from $brewfile"
    fi
}

update_homebrew() {
    if ! command_exists brew; then
        log_warning "Homebrew not installed, skipping update"
        return 1
    fi
    
    log_info "Updating Homebrew"
    if [[ "$DRY_RUN" != "true" ]]; then
        brew update && brew upgrade && brew cleanup
        log_success "Homebrew updated successfully"
    else
        log_info "[DRY RUN] Would update Homebrew"
    fi
}

# Stow functions
stow_package() {
    local package="$1"
    local target="${2:-$HOME}"
    local action="${3:-stow}"
    
    if [ ! -d "$DOTFILES_ROOT/$package" ]; then
        log_error "Package directory not found: $DOTFILES_ROOT/$package"
        return 1
    fi
    
    log_info "${action^}ing $package to $target"
    if [[ "$DRY_RUN" != "true" ]]; then
        cd "$DOTFILES_ROOT" || return 1
        case "$action" in
            "stow")
                stow --adopt -v --no-folding -t "$target" "$package"
                ;;
            "restow")
                stow --adopt -v --restow --no-folding -t "$target" "$package"
                ;;
            "unstow")
                stow -v -D -t "$target" "$package"
                ;;
            *)
                log_error "Unknown stow action: $action"
                return 1
                ;;
        esac
        log_success "$package ${action}ed successfully"
    else
        log_info "[DRY RUN] Would $action $package"
    fi
}

stow_all_packages() {
    local packages=("config" "shell" "git" "docker" "warp")
    local action="${1:-stow}"
    
    for package in "${packages[@]}"; do
        if [ -d "$DOTFILES_ROOT/$package" ]; then
            stow_package "$package" "$HOME" "$action"
        else
            log_warning "Package directory not found: $package, skipping"
        fi
    done
}

# Git functions
git_pull_updates() {
    log_info "Pulling latest changes from git repository"
    if [[ "$DRY_RUN" != "true" ]]; then
        cd "$DOTFILES_ROOT" || return 1
        git pull
        log_success "Git repository updated"
    else
        log_info "[DRY RUN] Would pull git updates"
    fi
}

# VS Code functions
sync_vscode_extensions() {
    if ! command_exists code; then
        log_warning "VS Code CLI not found, skipping extensions sync"
        return 1
    fi
    
    local extensions_file="$DOTFILES_ROOT/vscode/extensions.txt"
    log_info "Updating VS Code extensions list"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        ensure_dir "$(dirname "$extensions_file")"
        code --list-extensions > "$extensions_file"
        log_success "VS Code extensions list updated"
    else
        log_info "[DRY RUN] Would update VS Code extensions list"
    fi
}

install_vscode_extensions() {
    if ! command_exists code; then
        log_warning "VS Code CLI not found, skipping extensions installation"
        return 1
    fi
    
    local extensions_file="$DOTFILES_ROOT/vscode/extensions.txt"
    if [ ! -f "$extensions_file" ]; then
        log_error "Extensions file not found: $extensions_file"
        return 1
    fi
    
    log_info "Installing VS Code extensions from list"
    if [[ "$DRY_RUN" != "true" ]]; then
        while IFS= read -r extension; do
            if [[ -n "$extension" ]] && [[ ! "$extension" =~ ^# ]]; then
                log_info "Installing extension: $extension"
                code --install-extension "$extension" --force
            fi
        done < "$extensions_file"
        log_success "VS Code extensions installed"
    else
        log_info "[DRY RUN] Would install VS Code extensions"
    fi
}

# macOS functions
check_mas_signin() {
    if ! command_exists mas; then
        log_error "mas CLI not installed"
        return 1
    fi
    
    local mas_account
    mas_account=$(mas account 2>/dev/null || echo "")
    if [ -z "$mas_account" ]; then
        log_warning "Not signed in to Mac App Store"
        if [[ "$FORCE_YES" != "true" ]] && [[ "$DRY_RUN" != "true" ]]; then
            log_info "Please sign in to the Mac App Store"
            open -a "App Store"
            read -p "Press Enter when you have signed in to the Mac App Store... " -r
        fi
        return 1
    fi
    return 0
}

# CLI argument parsing
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
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
                return 2  # Special return code for help
                ;;
            *)
                # Unknown option, let calling script handle it
                break
                ;;
        esac
    done
    
    # Export variables for child scripts
    export VERBOSE DRY_RUN FORCE_YES DOTFILES_ROOT
}

# Error handling
die() {
    log_error "$1"
    exit "${2:-1}"
}

# Validation functions
validate_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        die "This script is designed for macOS only"
    fi
}

validate_dotfiles_root() {
    if [ ! -d "$DOTFILES_ROOT" ]; then
        die "Dotfiles root directory not found: $DOTFILES_ROOT"
    fi
    
    if [ ! -f "$DOTFILES_ROOT/bootstrap.sh" ]; then
        die "Invalid dotfiles directory: $DOTFILES_ROOT (bootstrap.sh not found)"
    fi
}

# Initialize function
init_utils() {
    validate_dotfiles_root
    log_debug "Utils initialized with DOTFILES_ROOT: $DOTFILES_ROOT"
}
