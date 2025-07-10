# dotfiles completion for zsh
# Uses cobra's built-in completion when available

if command -v dotfiles >/dev/null 2>&1; then
    source <(dotfiles completion zsh)
fi