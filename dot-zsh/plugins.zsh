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
    
    # Completions should be loaded first
    zinit ice wait lucid blockf
    zinit load zsh-users/zsh-completions
    
    # Load fzf-tab for interactive completion menu (must load before compinit)
    zinit ice wait lucid
    zinit load Aloxaf/fzf-tab
    
    # Initialize completions
    zinit ice wait lucid atinit"ZINIT[COMPINIT_OPTS]=-C; zicompinit; zicdreplay"
    
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
