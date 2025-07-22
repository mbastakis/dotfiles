#!/bin/bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLABORATORS_FILE="$SCRIPT_DIR/../.github/collaborators.yml"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI (gh) is not installed. Please install it first:"
    log_error "  brew install gh"
    log_error "  or visit: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    log_error "You are not authenticated with GitHub CLI."
    log_error "Please run: gh auth login"
    exit 1
fi

# Check if collaborators.yml exists
if [ ! -f "$COLLABORATORS_FILE" ]; then
    log_error "Collaborators configuration file not found: $COLLABORATORS_FILE"
    exit 1
fi

log_info "Managing repository collaborators..."
log_info "Using configuration file: $COLLABORATORS_FILE"

# Get current repository
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
log_info "Repository: $REPO"

log_step "Current collaborators:"
gh api repos/$REPO/collaborators | jq -r '.[] | "\(.login) - \(.permissions | to_entries | map(select(.value == true)) | map(.key) | join(", "))"' || log_warning "Could not list current collaborators"

log_step "Processing collaborators from configuration file..."

# Parse collaborators.yml and add collaborators
# Note: This is a simplified YAML parser. For production use, consider using yq
if command -v yq &> /dev/null; then
    # Use yq if available
    yq eval '.collaborators[] | .username + " " + .permission' "$COLLABORATORS_FILE" | while read username permission; do
        if [ ! -z "$username" ] && [ ! -z "$permission" ]; then
            log_info "Adding/updating collaborator: $username with permission: $permission"
            if gh api repos/$REPO/collaborators/$username --method PUT --field permission="$permission" --silent; then
                log_info "✓ Successfully updated $username"
            else
                log_error "✗ Failed to update $username"
            fi
        fi
    done
else
    # Fallback to basic grep/sed parsing
    log_warning "yq not found, using basic parsing. Install yq for better YAML parsing."
    grep -A 10 "collaborators:" "$COLLABORATORS_FILE" | grep -E "^\s*-\s*username:" | sed 's/.*username:\s*//' | while read username; do
        if [ ! -z "$username" ]; then
            permission=$(grep -A 5 "username: $username" "$COLLABORATORS_FILE" | grep "permission:" | sed 's/.*permission:\s*//' | head -1)
            log_info "Adding/updating collaborator: $username with permission: $permission"
            if gh api repos/$REPO/collaborators/$username --method PUT --field permission="$permission" --silent; then
                log_info "✓ Successfully updated $username"
            else
                log_error "✗ Failed to update $username"
            fi
        fi
    done
fi

log_step "Updated collaborators:"
gh api repos/$REPO/collaborators | jq -r '.[] | "\(.login) - \(.permissions | to_entries | map(select(.value == true)) | map(.key) | join(", "))"' || log_warning "Could not list updated collaborators"

log_info "Collaborator management completed!"