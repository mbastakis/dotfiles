# .zshrc - Main ZSH configuration file

# Load Starship prompt if installed
if command -v starship &> /dev/null; then
  eval "$(starship init zsh)"
fi

# Load custom configurations
for file in ~/.zsh/{aliases,exports,functions,plugins,local,config}*.zsh; do
  [ -r "$file" ] && [ -f "$file" ] && source "$file"
done
unset file

# Set ZSH options
setopt AUTO_CD           # Change directory without cd
setopt EXTENDED_HISTORY  # Record timestamp in history
setopt SHARE_HISTORY     # Share history between sessions
setopt HIST_IGNORE_DUPS  # Don't record duplicates
setopt HIST_IGNORE_SPACE # Don't record commands starting with space

# History configuration
HISTSIZE=10000
SAVEHIST=10000
HISTFILE=~/.zsh_history

# Completion system
autoload -Uz compinit
compinit

# Use fzf if installed
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

### Added by Zinit's installer
if [[ ! -f $HOME/.local/share/zinit/zinit.git/zinit.zsh ]]; then
    print -P "%F{33} %F{220}Installing %F{33}ZDHARMA-CONTINUUM%F{220} Initiative Plugin Manager (%F{33}zdharma-continuum/zinit%F{220})…%f"
    command mkdir -p "$HOME/.local/share/zinit" && command chmod g-rwX "$HOME/.local/share/zinit"
    command git clone https://github.com/zdharma-continuum/zinit "$HOME/.local/share/zinit/zinit.git" && \
        print -P "%F{33} %F{34}Installation successful.%f%b" || \
        print -P "%F{160} The clone has failed.%f%b"
fi

source "$HOME/.local/share/zinit/zinit.git/zinit.zsh"
autoload -Uz _zinit
(( ${+_comps} )) && _comps[zinit]=_zinit
### End of Zinit's installer chunk

# bun completions
[ -s "/Users/A200407315/.bun/_bun" ] && source "/Users/A200407315/.bun/_bun"

# Atuin shell history
eval "$(atuin init zsh)"

# Zoxide
eval "$(zoxide init zsh)"

# Thefuck
eval $(thefuck --alias)
