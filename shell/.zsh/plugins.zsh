# Zinit plugins management
# This file manages all ZSH plugins via Zinit

# Load and initialize zinit if installed
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
    
    # Initialize completions
    zinit ice wait lucid atinit"ZINIT[COMPINIT_OPTS]=-C; zicompinit; zicdreplay"
    
    # Completions should be loaded first
    zinit ice wait lucid blockf
    zinit load zsh-users/zsh-completions
    
    # Example: Useful utilities
    zinit ice wait"0" lucid
    zinit load zdharma-continuum/history-search-multi-word
    
    # Load Git plugin from Oh-My-Zsh
    zinit snippet OMZ::plugins/git/git.plugin.zsh
    
    # Load Kubectl plugin from Oh-My-Zsh
    zinit snippet OMZ::plugins/kubectl/kubectl.plugin.zsh

    # Load exa (modern replacement for ls)
    zinit ice wait"0" lucid from"gh-r" as"program" mv"bin/exa* -> exa" 
    zinit light ogham/exa

    # History substring search
    # Function to configure history substring search
    _history_substring_search_config() {
        # Bind up and down arrows
        bindkey '^[[A' history-substring-search-up
        bindkey '^[[B' history-substring-search-down
        
        # Bind k and j in vi mode
        bindkey -M vicmd 'k' history-substring-search-up
        bindkey -M vicmd 'j' history-substring-search-down
    }
    
    # Load history substring search with configuration
    zinit ice wait lucid atload'_history_substring_search_config'
    zinit load zsh-users/zsh-history-substring-search

    # Load autosuggestions (should be before syntax highlighting)
    zinit ice wait lucid atload'!_zsh_autosuggest_start'
    zinit load zsh-users/zsh-autosuggestions
    
    # Load syntax highlighting (must be last for proper highlighting)
    zinit ice wait lucid
    zinit load zdharma-continuum/fast-syntax-highlighting
    
    # Load your custom plugins below
    # zinit load <username>/<repository>
fi
