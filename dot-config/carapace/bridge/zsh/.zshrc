# Initialize completion system
autoload -U compinit && compinit -i

# Load tool completions
eval "$(bw completion --shell zsh)"
eval "$(opencode completion)"
[[ -s "$HOME/.bun/_bun" ]] && source "$HOME/.bun/_bun"

# Explicitly register completions (the #compdef directives are comments when eval'd)
compdef _bw bw
compdef _opencode_yargs_completions opencode
compdef _bun bun
