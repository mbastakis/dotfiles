# .zshenv - ZSH environment file loaded for all shell types (login, interactive, neither)
# This file should be kept as minimal as possible and only contain environment
# variables that need to be set for all shell types

# Ensure user-level bin directory exists and is in PATH
if [[ ! -d "$HOME/bin" ]]; then
    mkdir -p "$HOME/bin"
fi
