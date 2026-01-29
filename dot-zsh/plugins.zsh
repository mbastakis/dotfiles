#!/usr/bin/env zsh
# plugins.zsh - Zinit plugins management

# Auto-install zinit if not present
if [[ ! -f "${HOME}/.local/share/zinit/zinit.git/zinit.zsh" ]]; then
    print -P "%F{33}Installing %F{220}zinit%F{33}...%f"
    command mkdir -p "${HOME}/.local/share/zinit" && command chmod g-rwX "${HOME}/.local/share/zinit"
    command git clone https://github.com/zdharma-continuum/zinit "${HOME}/.local/share/zinit/zinit.git" && \
        print -P "%F{34}Installation successful.%f" || \
        print -P "%F{160}Clone failed.%f"
fi

# Load and initialize zinit
if [[ -f "${HOME}/.local/share/zinit/zinit.git/zinit.zsh" ]]; then
    source "${HOME}/.local/share/zinit/zinit.git/zinit.zsh"
    autoload -Uz _zinit
    (( ${+_comps} )) && _comps[zinit]=_zinit

    # Load a few important annexes, without Turbo
    # (this is currently required for annexes)
    zinit light-mode for \
        zdharma-continuum/zinit-annex-as-monitor \
        zdharma-continuum/zinit-annex-bin-gem-node \
        zdharma-continuum/zinit-annex-patch-dl \
        zdharma-continuum/zinit-annex-rust

    # ==== Plugin Definitions ====
    # Add your plugins below
    
    # Completions should be loaded first
    zinit ice blockf
    zinit load zsh-users/zsh-completions
    
    # Load fzf-tab for interactive completion menu (must load before compinit)
    zinit light Aloxaf/fzf-tab
    
    # Initialize completions (carapace must be loaded AFTER this - see dot-zshrc)
    # Cache compinit - only rebuild dump file once per day for faster startup
    # Glob qualifier: N=no error if no match, .=regular file, mh+24=modified >24h ago
    autoload -Uz compinit
    if [[ -f ~/.zcompdump && $(find ~/.zcompdump -mtime -1 2>/dev/null) ]]; then
      compinit -C  # Cache is fresh (<24h), use it
    else
      compinit     # Cache is stale (>24h) or missing, rebuild
    fi
    
    # Load Git plugin from Oh-My-Zsh
    zinit snippet OMZ::plugins/git/git.plugin.zsh
    
    # Load Kubectl plugin from Oh-My-Zsh
    zinit snippet OMZ::plugins/kubectl/kubectl.plugin.zsh

    # Load autosuggestions (should be before syntax highlighting)
    zinit ice wait lucid atload'!_zsh_autosuggest_start'
    zinit load zsh-users/zsh-autosuggestions
    
    # Load shift-select functionality (Shift+arrows to select text)
    # Load our enhancements after the plugin loads using atload hook
    zinit ice wait lucid atload'source "${ZDOTDIR:-$HOME}/.zsh/shift-select-enhancements.zsh"'
    zinit load jirutka/zsh-shift-select
    
    # Load syntax highlighting (must be last for proper highlighting)
    zinit ice wait lucid
    zinit load zdharma-continuum/fast-syntax-highlighting
fi
