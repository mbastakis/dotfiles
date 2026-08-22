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

    # ==== Plugin Definitions ====

    # Load fzf-tab for interactive completion menu (must load before compinit)
    zinit light Aloxaf/fzf-tab

    # Initialize package-managed completions before sourcing generated scripts.
    # Cache compinit - only rebuild dump file once per day for faster startup
    # Glob qualifier: N=no error if no match, .=regular file, mh+24=modified >24h ago
    if (( ${+_comps} )); then
      : # compinit already initialized (e.g. by system zshrc)
    else
      autoload -Uz compinit
      _zcompdump="${ZDOTDIR:-$HOME}/.zcompdump"
      if [[ -f "$_zcompdump" && $(find "$_zcompdump" -mtime -1 2>/dev/null) ]]; then
        compinit -C -d "$_zcompdump"  # Cache is fresh (<24h), use it
      else
        compinit -d "$_zcompdump"     # Cache is stale (>24h) or missing, rebuild
      fi
      unset _zcompdump
    fi

    # Load Git plugin from Oh-My-Zsh
    zinit snippet OMZ::plugins/git/git.plugin.zsh

    # Load autosuggestions (should be before syntax highlighting)
    zinit ice wait lucid atload'!unset ZSH_AUTOSUGGEST_USE_ASYNC; _zsh_autosuggest_start'
    zinit load zsh-users/zsh-autosuggestions

    # Load syntax highlighting (must be last for proper highlighting)
    # Paths in typed commands stay default-colored (F-Sy-H defaults them to
    # ANSI magenta, which the theme renders as rose — reserved for focus).
    zinit ice wait lucid atload'FAST_HIGHLIGHT_STYLES[path]=fg=default; FAST_HIGHLIGHT_STYLES[path-to-dir]=fg=default,underline; FAST_HIGHLIGHT_STYLES[path_pathseparator]=fg=default; FAST_HIGHLIGHT_STYLES[path-to-dir_pathseparator]=fg=default,underline'
    zinit load zdharma-continuum/fast-syntax-highlighting
fi
