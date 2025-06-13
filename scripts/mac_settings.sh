#!/bin/bash
#
# Script to configure macOS system preferences and settings
# 
# Author: mbastakis
# Last updated: April 22, 2025
#

# Exit on error, undefined variable, and prevent errors in pipelines from being masked
set -euo pipefail 
IFS=$'\n\t'

# Include utility functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit
source "$SCRIPT_DIR/utils.sh"

###################
# Global Variables #
###################

# Computer name to set
COMPUTER_NAME="cerebro"

# Execute command with error handling
execute() {
    local cmd="$1"
    local msg="${2:-Executing command}"
    
    log_info "$msg"
    if eval "$cmd"; then
        return 0
    else
        local exit_code=$?
        log_error "Command failed with exit code $exit_code: $cmd"
        return $exit_code
    fi
}

##################
# Feature Functions 
##################

# Set computer name and hostname
set_computer_name() {
    log_section "Setting Computer Name"
    
    execute "sudo scutil --set ComputerName \"$COMPUTER_NAME\"" "Setting computer name to $COMPUTER_NAME"
    execute "sudo scutil --set HostName \"$COMPUTER_NAME\"" "Setting host name to $COMPUTER_NAME"
    execute "sudo scutil --set LocalHostName \"$COMPUTER_NAME\"" "Setting local host name to $COMPUTER_NAME"
    execute "sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.smb.server NetBIOSName -string \"$COMPUTER_NAME\"" "Setting NetBIOS name to $COMPUTER_NAME"
}

# Configure dock settings
configure_dock() {
    log_section "Configuring Dock"
    
    execute "defaults write com.apple.dock \"orientation\" -string \"right\"" "Setting dock orientation to right"
    execute "defaults write com.apple.dock \"tilesize\" -int \"56\"" "Setting dock tile size to 56"
    execute "defaults write com.apple.dock \"autohide\" -bool \"true\"" "Enabling dock auto-hide"
    execute "defaults write com.apple.dock \"autohide-time-modifier\" -float \"0\"" "Setting dock hide time to immediate"
    execute "defaults write com.apple.dock \"autohide-delay\" -float \"0\"" "Setting dock hide delay to 0"
    execute "defaults write com.apple.dock \"show-recents\" -bool \"false\"" "Disabling recent apps in dock"
    execute "defaults write com.apple.dock \"mineffect\" -string \"scale\"" "Setting dock minimize effect to scale"
}

# Configure finder settings
configure_finder() {
    log_section "Configuring Finder"
    
    execute "defaults write NSGlobalDomain \"AppleShowAllExtensions\" -bool \"true\"" "Showing all file extensions"
    execute "defaults write com.apple.finder \"AppleShowAllFiles\" -bool \"true\"" "Showing hidden files"
    execute "defaults write com.apple.finder \"ShowPathbar\" -bool \"true\"" "Showing path bar"
    execute "defaults write com.apple.finder \"FXPreferredViewStyle\" -string \"Nlsv\"" "Setting list view as default"
    execute "defaults write com.apple.finder \"_FXSortFoldersFirst\" -bool \"true\"" "Setting folders to appear first"
    execute "defaults write com.apple.finder \"FXDefaultSearchScope\" -string \"SCcf\"" "Setting default search scope to current folder"
    execute "defaults write NSGlobalDomain \"NSTableViewDefaultSizeMode\" -int \"3\"" "Setting default column width"
    
    execute "chflags nohidden ~/Library" "Showing Library folder"
}

# Configure screenshot settings
configure_screenshots() {
    log_section "Configuring Screenshots"
    
    execute "defaults write com.apple.screencapture disable-shadow -bool true" "Disabling screenshot shadows"
}

# Configure bluetooth settings
configure_bluetooth() {
    log_section "Configuring Bluetooth"
    
    execute "defaults write com.apple.BluetoothAudioAgent \"Apple Bitpool Min (editable)\" -int 40" "Setting Bluetooth headset higher bit rate"
}

# Configure trackpad settings
configure_trackpad() {
    log_section "Configuring Trackpad"
    
    execute "defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true" "Enabling tap to click"
    execute "defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1" "Enabling tap to click for current host"
    execute "defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1" "Enabling tap to click for login screen"
}

# Configure keyboard settings
configure_keyboard() {
    log_section "Configuring Keyboard"
    
    execute "defaults write NSGlobalDomain AppleKeyboardUIMode -int 3" "Enabling full keyboard access for all controls"
}

# Configure display settings
configure_display() {
    log_section "Configuring Display"
    
    execute "defaults write NSGlobalDomain AppleFontSmoothing -int 2" "Enabling subpixel font rendering on non-Retina displays"
    execute "defaults write NSGlobalDomain AppleHighlightColor -string \"0.764700 0.568600 0.976500\"" "Setting highlight color to purple"
}

# Configure UI/UX settings
configure_ui_ux() {
    log_section "Configuring UI/UX Settings"
    
    execute "defaults write NSGlobalDomain AppleShowScrollBars -string \"WhenScrolling\"" "Setting scrollbars to show when scrolling"
    execute "defaults write com.apple.LaunchServices LSQuarantine -bool false" "Disabling 'Are you sure you want to open this application?' dialog"
    
    log_info "Removing duplicates in the 'Open With' menu"
    execute "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user" "Cleaning 'Open With' menu"
}

# Configure text input settings
configure_text_input() {
    log_section "Configuring Text Input Settings"
    
    execute "defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false" "Disabling automatic capitalization"
    execute "defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false" "Disabling smart dashes"
    execute "defaults write NSGlobalDomain NSAutomaticPeriodSubstitutionEnabled -bool false" "Disabling automatic period substitution"
    execute "defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false" "Disabling smart quotes"
    execute "defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false" "Disabling auto-correct"
}

# Configure date and time settings
configure_datetime() {
    log_section "Configuring Date & Time Settings"
    
    execute "defaults write com.apple.menuextra.clock \"DateFormat\" -string \"\\\"EEE d MMM HH:mm:ss\\\"\"" "Setting menu bar clock format"
}

# Configure accessibility settings
configure_accessibility() {
    log_section "Configuring Accessibility Settings"
    
    execute "sudo defaults write com.apple.universalaccess closeViewScrollWheelToggle -bool true" "Enabling zoom with ctrl+scroll"
    execute "sudo defaults write com.apple.universalaccess HIDScrollZoomModifierMask -int 262144" "Setting zoom modifier key to ctrl"
    execute "sudo defaults write com.apple.universalaccess closeViewZoomFollowsFocus -bool true" "Enabling zoom follows focus"
}

# Apply changes by restarting system processes
apply_changes() {
    log_section "Applying Changes"
    
    log_info "Restarting system services to apply changes"
    for app in Finder Dock SystemUIServer cfprefsd; do
        execute "killall \"$app\" >/dev/null 2>&1 || true" "Restarting $app"
    done
}

# Show help information
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Script to configure macOS system preferences and settings"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message and exit"
    echo "  -n, --name NAME     Set computer name to NAME"
    echo "  --no-restart        Don't restart system processes"
    echo ""
    echo "Examples:"
    echo "  $0                  Apply all settings with default values"
    echo "  $0 -n macbook-pro   Apply all settings and set computer name to macbook-pro"
    echo "  $0 --no-restart     Apply all settings without restarting system processes"
}

# Parse command line arguments
parse_arguments() {
    RESTART=true
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -n|--name)
                if [[ -z "$2" ]]; then
                    log_error "Computer name not provided"
                    show_help
                    exit 1
                fi
                COMPUTER_NAME="$2"
                shift 2
                ;;
            --no-restart)
                RESTART=false
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Main function
main() {
    log_info "macOS Settings Configuration Script started"
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Apply settings
    # set_computer_name
    configure_dock
    configure_finder
    configure_screenshots
    configure_bluetooth
    configure_trackpad
    configure_keyboard
    configure_display
    configure_ui_ux
    configure_text_input
    configure_datetime
    configure_accessibility
    
    # Apply changes if not disabled
    if [[ "$RESTART" == true ]]; then
        apply_changes
    else
        log_warning "System processes restart skipped. Some changes may not take effect until next restart."
    fi
    
    log_info "macOS Settings Configuration Script completed successfully!"
}

# Run main function with all arguments
main "$@"