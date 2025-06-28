#!/bin/bash
#
# Homebrew installation script
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

# Main installation function
main() {
    log_section "Homebrew Installation"
    
    # Parse command line arguments
    parse_args "$@"
    if [[ $? -eq 2 ]]; then
        show_help
        exit 0
    fi
    
    # Install Homebrew
    install_homebrew
    
    log_section "Homebrew Installation Complete"
}

# Help function
show_help() {
    cat << EOF
Homebrew Installation Script

Usage: $0 [OPTIONS]

Options:
    -v, --verbose    Enable verbose output
    -y, --yes        Answer yes to all prompts
    --dry-run        Show what would be done without executing
    -h, --help       Show this help message

Examples:
    $0                    # Interactive installation
    $0 -y                 # Auto-install without prompts
    $0 --dry-run          # Preview what would be installed
EOF
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi