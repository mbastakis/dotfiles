# exports.zsh - Environment variables

# Default programs
export EDITOR="nvim"
export VISUAL="code --wait"
export PAGER="bat"

# Path configuration
# Add your custom paths here
export PATH="$HOME/.local/bin:$PATH"

# Add Homebrew sbin to PATH
export PATH="/usr/local/sbin:$PATH"

# Programming language environments

# Python
export PYTHONDONTWRITEBYTECODE=1  # Don't write .pyc files

# Go
export GOPATH="$HOME/go"
export PATH="$GOPATH/bin:$PATH"

# Language preference
export LANG="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"

# Less settings
export LESS="-R"
export LESS_TERMCAP_mb=$'\E[1;31m'     # begin blink
export LESS_TERMCAP_md=$'\E[1;36m'     # begin bold
export LESS_TERMCAP_me=$'\E[0m'        # reset bold/blink
export LESS_TERMCAP_so=$'\E[01;44;33m' # begin reverse video
export LESS_TERMCAP_se=$'\E[0m'        # reset reverse video
export LESS_TERMCAP_us=$'\E[1;32m'     # begin underline
export LESS_TERMCAP_ue=$'\E[0m'        # reset underline

# Exa path
export PATH="$HOME/.local/share/zinit/plugins/ogham---exa/bin:$PATH"

# Dotfiles path
export DOTFILES_PATH="$HOME/dev/dotfiles"
