# aliases.zsh - Shell aliases

# Navigation
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."

# Listing
# Using exa if available, fallback to standard ls if not
if (( $+commands[exa] )); then
    alias ls="exa"
    alias ll="exa -la"
    alias la="exa -a"
    alias l="exa -l"
    alias lt="exa -T"  # Tree view
    alias lg="exa -l --git"  # Show git status
else
    alias ls="ls -G"
    alias ll="ls -la"
    alias la="ls -a"
    alias l="ls -lh"
fi

# Utilities
alias reload="source ~/.zshrc"
alias brewup="brew update && brew upgrade && brew cleanup"
alias dotfiles="cd ~/.dotfiles"

# Vim
alias v="nvim"
alias vi="nvim"
alias vim="nvim"
