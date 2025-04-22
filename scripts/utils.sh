#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log info message with timestamp
log_info() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1"
}

# Log warning message with timestamp
log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING]${NC} $1"
}

# Log error message with timestamp
log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1"
}

# Log section heading
log_section() {
    echo -e "\n${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] [SECTION] $1 ${NC}"
    echo -e "${BLUE}----------------------------------------${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Create directory if it doesn't exist
ensure_dir() {
    if [ ! -d "$1" ]; then
        log_info "Creating directory: $1"
        mkdir -p "$1"
    fi
}

# Backup file if it exists
backup_file() {
    if [ -f "$1" ]; then
        local backup_file
        backup_file="$1.backup.$(date +%Y%m%d%H%M%S)"
        log_info "Backing up $1 to $backup_file"
        cp "$1" "$backup_file"
    fi
}

# Check for root/sudo access
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        log_info "Some operations require sudo access"
        sudo -v
        # Keep sudo alive
        while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &
    fi
}
