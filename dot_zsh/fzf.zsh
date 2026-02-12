#!/usr/bin/env zsh
# fzf.zsh - Consolidated fzf configuration
#
# Pattern: FZF_DEFAULT_OPTS contains all base settings (colors, bindings, UI).
# Tool-specific configs ONLY override what's different from defaults.

# =============================================================================
# BASE CONFIGURATION (applied to ALL fzf invocations automatically)
# =============================================================================

# Catppuccin Mocha colors
FZF_COLORS="\
--color=bg+:#313244,bg:#1E1E2E,spinner:#F5E0DC,hl:#F38BA8 \
--color=fg:#CDD6F4,header:#F38BA8,info:#CBA6F7,pointer:#F5E0DC \
--color=marker:#B4BEFE,fg+:#CDD6F4,prompt:#CBA6F7,hl+:#F38BA8 \
--color=selected-bg:#45475A \
--color=border:#6C7086,label:#CDD6F4"

# Keybindings
FZF_BINDS="\
--bind='ctrl-/:toggle-preview' \
--bind='ctrl-d:preview-page-down' \
--bind='ctrl-u:preview-page-up' \
--bind='ctrl-y:execute-silent(echo -n {} | pbcopy)' \
--bind='ctrl-a:toggle-all' \
--bind='ctrl-s:toggle-sort'"

# UI elements
FZF_UI="\
--border=rounded \
--padding=0,1 \
--prompt=' ' \
--pointer='→' \
--marker=' ' \
--cycle \
--scrollbar='│'"

# Combined defaults - automatically applied to all fzf invocations
export FZF_DEFAULT_OPTS="\
$FZF_COLORS \
$FZF_BINDS \
$FZF_UI \
--height=~40 \
--layout=reverse \
--info='inline: ' \
--multi"

# =============================================================================
# DEFAULT COMMAND (what files to search)
# =============================================================================
# --no-ignore-vcs: include gitignored files
# --exclude: explicit excludes for dirs we never want
export FZF_DEFAULT_COMMAND='fd --type f --strip-cwd-prefix --hidden --follow --no-ignore-vcs \
  --exclude .git \
  --exclude node_modules \
  --exclude .venv \
  --exclude __pycache__ \
  --exclude .cache \
  --exclude dist \
  --exclude build \
  --exclude target \
  --exclude .next \
  --exclude .nuxt'

# =============================================================================
# CTRL-T: File picker (overrides: preview, label)
# =============================================================================
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_CTRL_T_OPTS="\
--border-label=' Select file ' \
--preview='bat -n --color=always --line-range :500 {}' \
--preview-window='right,50%,border-left'"

# =============================================================================
# ALT-C: Disabled (using zoxide instead)
# =============================================================================
export FZF_ALT_C_COMMAND=""

# =============================================================================
# CTRL-R: History search (overrides: preview, header, label)
# Note: atuin takes precedence if loaded
# =============================================================================
export FZF_CTRL_R_OPTS="\
--border-label=' History ' \
--preview='echo {}' \
--preview-window='up:3:hidden:wrap' \
--header='CTRL-Y to copy'"

# =============================================================================
# ZOXIDE: Directory jump (overrides: height, sort, preview, label)
# Note: _ZO_FZF_OPTS completely replaces defaults, so we must include base
# =============================================================================
export _ZO_FZF_OPTS="\
$FZF_DEFAULT_OPTS \
--height=~20 \
--no-sort \
--border-label=' Jump to directory ' \
--preview='eza --icons --color=always --group-directories-first --git {2..} 2>/dev/null; \
branch=\$(cd {2..} && git rev-parse --abbrev-ref HEAD 2>/dev/null) && \
w=\${FZF_PREVIEW_COLUMNS:-80} && \
line=\"──────────────────────────────────\" && \
txt=\"  \$branch\" && \
printf \"\n%*s\n%*s\n\" \$(((w+\${#line})/2)) \"\$line\" \$(((w+\${#txt})/2)) \"\$txt\"' \
--preview-window='bottom,6,border-top'"

# =============================================================================
# FTEXT: Ripgrep search (overrides: layout, preview, delimiter)
# Note: Array format because fzf is invoked directly in functions.zsh
# FZF_DEFAULT_OPTS is still auto-applied, so we only specify overrides.
# =============================================================================
_ftext_fzf_opts=(
  --layout=default
  --border-label=' Search in files '
  --delimiter=:
  --preview='bat --color=always {1} --highlight-line {2} 2>/dev/null'
  --preview-window='up,70%,border-bottom,+{2}+3/3,~3'
)

# =============================================================================
# INITIALIZE FZF
# =============================================================================
if command -v fzf &>/dev/null; then
  # fzf --zsh installs ZLE widgets/bindings and warns in non-TTY shells
  # (e.g. zsh -i -c ...). Skip widget init unless attached to a terminal.
  if [[ -t 0 && -t 1 ]]; then
    eval "$(fzf --zsh)"
    # Unbind fzf's Ctrl+R to let atuin handle it
    bindkey -r '^R'
  fi
fi

# =============================================================================
# ATUIN: Shell history (loaded after fzf so it binds Ctrl+R)
# =============================================================================
command -v atuin &>/dev/null && eval "$(atuin init zsh)"
