#!/bin/bash
# .zprofile - Executed for login shells (after zshenv, before zshrc)
# This is similar to .profile for Bash, used for login shells

# This file is kept intentionally minimal
# Most configuration should go in .zshrc for interactive shells
# or in .zshenv for environment variables needed by all shell types

# Add any login-specific configurations here

eval "$(/opt/homebrew/bin/brew shellenv)"

# Autojump
[ -f /opt/homebrew/etc/profile.d/autojump.sh ] && . /opt/homebrew/etc/profile.d/autojump.sh
