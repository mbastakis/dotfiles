#!/usr/bin/env zsh
# functions.zsh - Custom shell functions

# Extract almost any archive
extract() {
  if [ -f "$1" ]; then
    case "$1" in
    *.tar.bz2) tar xjf "$1" ;;
    *.tar.gz) tar xzf "$1" ;;
    *.bz2) bunzip2 "$1" ;;
    *.rar) unrar e "$1" ;;
    *.gz) gunzip "$1" ;;
    *.tar) tar xf "$1" ;;
    *.tbz2) tar xjf "$1" ;;
    *.tgz) tar xzf "$1" ;;
    *.zip) unzip "$1" ;;
    *.Z) uncompress "$1" ;;
    *.7z) 7z x "$1" ;;
    *) echo "'$1' cannot be extracted via extract()" ;;
    esac
  else
    echo "'$1' is not a valid file"
  fi
}

# Find process by name and kill it
killname() {
  ps aux | grep "$1" | grep -v grep | awk '{print $2}' | xargs kill -9
}

# Make directory and enter it.
take() {
  mkdir "$1"
  cd "$1" || return
}

# Python virtual environment
# Create a venv
venv() {
  mkdir -p ~/.virtualenvs

  python3 -m venv ~/.virtualenvs/$1
}
# Activate python environment
activate() {
  source ~/.virtualenvs/$1/bin/activate
}
deact() {
  deactivate
}
venvlist() {
  ls ~/.virtualenvs/
}
venvremove() {
  sudo rm -rf ~/.virtualenvs/$1
}

# Yazi
function y() {
  local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
  yazi "$@" --cwd-file="$tmp"
  IFS= read -r -d '' cwd <"$tmp"
  [ -n "$cwd" ] && [ "$cwd" != "$PWD" ] && cd -- "$cwd"
  rm -f -- "$tmp"
}

# Helper to open file in editor at specific line
_ftext_open_editor() {
  local file="$1" line="$2"
  if [[ -n "$VISUAL" ]]; then
    if [[ "$VISUAL" == *"code"* ]]; then
      code --user-data-dir ~/.vscode --goto "${file}:${line}"
    else
      eval "$VISUAL \"+${line}\" \"${file}\""
    fi
  else
    echo "VISUAL editor not set. File: ${file}:${line}"
  fi
}

ftext() {
  # Interactive ripgrep search with fzf
  local selected
  selected=$(rg --color=always --line-number --no-heading --smart-case "${*:-}" 2>/dev/null |
    fzf --ansi "${_ftext_fzf_opts[@]}")

  if [[ -n "$selected" ]]; then
    local file=$(echo "$selected" | cut -d: -f1)
    local line=$(echo "$selected" | cut -d: -f2)
    _ftext_open_editor "$file" "$line"
  fi
}

# ZLE widget version of ftext for CTRL-F keybinding
ftext-widget() {
  local original_buffer="$BUFFER"
  local original_cursor="$CURSOR"

  local result
  result=$(rg --color=always --line-number --no-heading --smart-case "" 2>/dev/null |
    fzf --ansi "${_ftext_fzf_opts[@]}" \
      --expect=tab)

  local key=$(echo "$result" | head -n1)
  local selected=$(echo "$result" | tail -n1)

  if [[ -n "$selected" ]]; then
    local file=$(echo "$selected" | cut -d: -f1)
    local line=$(echo "$selected" | cut -d: -f2)

    if [[ "$key" == "tab" ]]; then
      BUFFER="${original_buffer:0:$original_cursor}${file}${original_buffer:$original_cursor}"
      CURSOR=$((original_cursor + ${#file}))
      zle reset-prompt
    else
      BUFFER=""
      zle reset-prompt
      zle -I
      _ftext_open_editor "$file" "$line"
      zle reset-prompt
    fi
  else
    BUFFER="$original_buffer"
    CURSOR="$original_cursor"
    zle reset-prompt
  fi
}

# Update brew
function brew_update() {
  brew update
  brew upgrade
  brew cleanup
  brew doctor
  brew missing
  brew outdated
  brew autoremove
  echo "Homebrew update complete."
}

# Pull all git repos in a directory tree (parallel, with formatted output)
# Usage: git_pull_all [directory] [parallelism]
git_pull_all() {
  local search_dir="${1:-.}"
  local parallelism="${2:-8}"

  if [[ ! -d "$search_dir" ]]; then
    echo "Error: Directory '$search_dir' does not exist"
    return 1
  fi

  # Get absolute path upfront (use builtin cd to bypass hooks)
  local abs_dir
  abs_dir=$(builtin cd "$search_dir" && pwd)

  # Count repos first
  local repo_count
  repo_count=$(find "$abs_dir" -name ".git" -type d 2>/dev/null | wc -l | tr -d ' ')

  if [[ "$repo_count" -eq 0 ]]; then
    echo "No git repositories found in $search_dir"
    return 0
  fi

  echo "Pulling $repo_count repositories in $abs_dir (parallelism: $parallelism)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Create a temporary script for xargs to call
  local tmp_script
  tmp_script=$(mktemp)
  cat >"$tmp_script" <<'PULLSCRIPT'
#!/bin/sh
repo_dir="$1"
base_dir_len="$2"

cd "$repo_dir" || exit 1

# Get relative path by cutting the base directory prefix (using character count)
if [ "$base_dir_len" -gt 0 ]; then
  # Cut base_dir + 1 (for the trailing slash)
  rel_path=$(echo "$repo_dir" | cut -c$((base_dir_len + 2))-)
fi
if [ -z "$rel_path" ]; then
  rel_path="."
fi

# Perform the pull
result=$(git pull --ff-only 2>&1)
status=$?
msg=$(echo "$result" | tail -1)

# Format output based on result
if [ $status -eq 0 ]; then
  if echo "$result" | grep -q "Already up to date"; then
    printf "\033[32m✓\033[0m %-60s %s\n" "$rel_path" "$msg"
  else
    printf "\033[34m↓\033[0m %-60s \033[34m%s\033[0m\n" "$rel_path" "Updated"
  fi
else
  printf "\033[31m✗\033[0m %-60s \033[31m%s\033[0m\n" "$rel_path" "$msg"
fi
PULLSCRIPT
  chmod +x "$tmp_script"

  # Get length of abs_dir for the script to use
  local abs_dir_len=${#abs_dir}

  # Sort repos first, then process in parallel with live output (no final sort)
  find "$abs_dir" -name ".git" -type d 2>/dev/null |
    while read -r git_dir; do dirname "$git_dir"; done |
    sort |
    xargs -P "$parallelism" -I {} "$tmp_script" "{}" "$abs_dir_len"

  # Cleanup
  rm -f "$tmp_script"

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Done!"
}

# Opencode
OC_SERVER="http://localhost:4096"

oc() {
  opencode attach "$OC_SERVER" --dir .
}

occ() {
  local session_id
  session_id=$(opencode session list -n 1 --format json | jq -r '.[0].id')
  if [[ -n "$session_id" && "$session_id" != "null" ]]; then
    opencode attach "$OC_SERVER" --dir . -s "$session_id"
  else
    echo "No previous session found"
    return 1
  fi
}

ocr() {
  opencode run --attach "$OC_SERVER" -m amazon-bedrock/anthropic.claude-haiku-4-5-20251001-v1:0 "$@"
}
