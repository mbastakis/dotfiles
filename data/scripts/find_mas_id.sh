#!/bin/bash
#
# Mac App Store ID finder script
#
# Author: mbastakis
# Last updated: $(date '+%Y-%m-%d')
#

set -euo pipefail
IFS=$'\n\t'

# Include utility functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

# Initialize utils
init_utils

# Main function
main() {
    log_section "Mac App Store ID Finder"
    
    # Parse command line arguments
    local app_name=""
    local limit=10
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -l|--limit)
                limit="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                app_name="$1"
                shift
                ;;
        esac
    done
    
    # Validate arguments
    if [ -z "$app_name" ]; then
        log_error "App name is required"
        show_help
        exit 1
    fi
    
    # Check if mas is installed
    if ! command_exists mas; then
        log_error "mas CLI is not installed"
        log_info "Install it with: brew install mas"
        exit 1
    fi
    
    # Search for the app
    log_info "Searching Mac App Store for: $app_name"
    echo ""
    
    local search_results
    search_results=$(mas search "$app_name" | head -n "$limit")
    
    if [ -z "$search_results" ]; then
        log_warning "No apps found matching: $app_name"
        exit 1
    fi
    
    echo "$search_results"
    echo ""
    
    log_info "To install an app, add the following line to homebrew/Brewfile.mas:"
    echo "mas \"$app_name\", id: APP_ID"
    echo ""
    log_info "Or use: mas install APP_ID"
}

# Help function
show_help() {
    cat << EOF
Mac App Store ID Finder

Usage: $0 [OPTIONS] "App Name"

Options:
    -l, --limit NUM   Limit search results (default: 10)
    -h, --help        Show this help message

Examples:
    $0 "Amphetamine"           # Search for Amphetamine
    $0 -l 5 "Xcode"           # Search for Xcode, show 5 results
EOF
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
