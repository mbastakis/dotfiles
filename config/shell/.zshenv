# .zshenv - ZSH environment file loaded for all shell types (login, interactive, neither)
# This file should be kept as minimal as possible and only contain environment
# variables that need to be set for all shell types

# Set XDG base directories
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CACHE_HOME="$HOME/.cache"

# Ensure user-level bin directory exists and is in PATH
if [[ ! -d "$HOME/bin" ]]; then
    mkdir -p "$HOME/bin"
fi

# Set PATH so it includes user's private bin if it exists
if [[ -d "$HOME/bin" ]] ; then
    PATH="$HOME/bin:$PATH"
fi

# Set PATH so it includes user's private bin if it exists
if [[ -d "$HOME/.local/bin" ]] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
