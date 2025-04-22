#!/bin/bash
# Script to help find Mac App Store app IDs
# Example usage: ./find_mas_id.sh "Amphetamine"
# TODO: start using this script in the Brewfile.mas
set -euo pipefail
IFS=$'\n\t'

# Check if mas is installed
if ! command -v mas &> /dev/null; then
    echo "Error: mas CLI is not installed"
    echo "Install it with: brew install mas"
    exit 1
fi

# Check if an argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 \"App Name\""
    echo "Example: $0 \"Amphetamine\""
    exit 1
fi

echo "Searching Mac App Store for: $1"
mas search "$1" | head -n 10
echo ""
echo "To install an app, add the following line to homebrew/Brewfile.mas:"
echo "mas \"$1\", id: APP_ID"
