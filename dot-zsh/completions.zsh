#!/usr/bin/env zsh
# completions.zsh - Tool completions
# Loaded AFTER compinit (which runs in plugins.zsh)

# Bun completions
[[ -s "$HOME/.bun/_bun" ]] && source "$HOME/.bun/_bun"

# ==== Lazy-loaded completions ====
# These tools have slow completion init (1-2s each), so we defer loading
# until the user actually tries to complete them.

# Bitwarden CLI completions (lazy-loaded: ~1.7s init time)
if command -v bw &>/dev/null; then
  _bw_lazy() {
    unfunction _bw_lazy
    eval "$(bw completion --shell zsh)"
    compdef _bw bw
    _bw "$@"
  }
  compdef _bw_lazy bw
fi

# OpenCode completions (lazy-loaded: ~0.5s init time)
if command -v opencode &>/dev/null; then
  _opencode_lazy() {
    unfunction _opencode_lazy
    eval "$(opencode completion)"
    _opencode "$@"
  }
  compdef _opencode_lazy opencode
fi

# ==== Normal completions ====

# Obsidian CLI completions (~34ms, fast enough to load normally)
command -v obsidian-cli &>/dev/null && eval "$(obsidian-cli completion zsh)"
