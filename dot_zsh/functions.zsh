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

# AWS profile switcher - wraps Go binary to enable env var export
# Usage: aws-login <profile> [mfa-code] [options]
aws-login() {
  local output
  output=$("$HOME/bin/_aws-login" "$@")
  local exit_code=$?

  if [[ $exit_code -eq 0 && -n "$output" ]]; then
    eval "$output"

    if [[ -n "${TMUX:-}" ]] && command -v tmux &>/dev/null; then
      if [[ -n "${AWS_PROFILE:-}" ]]; then
        tmux set-environment -g AWS_PROFILE "$AWS_PROFILE"
      else
        tmux set-environment -gu AWS_PROFILE
      fi

      if [[ -n "${AWS_DEFAULT_PROFILE:-}" ]]; then
        tmux set-environment -g AWS_DEFAULT_PROFILE "$AWS_DEFAULT_PROFILE"
      else
        tmux set-environment -gu AWS_DEFAULT_PROFILE
      fi
    fi
  fi

  return $exit_code
}

function reset_internet() {
  sudo killall -HUP mDNSResponder && echo macOS DNS Cache Reset
  sudo pfctl -f /etc/pf.conf
  sudo ifconfig en0 down && sudo ifconfig en0 up
}
