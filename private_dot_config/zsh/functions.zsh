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

# Clear downloaded Python packages; installed environments remain intact.
function clean_uv() {
  uv cache clean
}

# Clear npm downloads and installed npx environments. Run when npx tools are idle.
function clean_npm() {
  local cache
  cache=$(npm config get cache) || return
  [[ "$cache" == /* && "$cache" != / ]] || return 1
  npm cache clean --force || return
  rm -rf -- "$cache/_npx"
}

# Clear Homebrew's downloaded packages, retaining installed packages.
function clean_homebrew() {
  local cache
  cache=$(brew --cache) || return
  [[ "$cache" == /* && "$cache" != / ]] || return 1
  local -a entries=("$cache"/*(DN))
  (( ${#entries} )) || return 0
  rm -rf -- "${entries[@]}"
}

# Clear Xcode build outputs and indexes. Run when builds are idle.
function clean_xcode() {
  local cache="$HOME/Library/Developer/Xcode/DerivedData"
  local -a entries=("$cache"/*(DN))
  (( ${#entries} )) || return 0
  rm -rf -- "${entries[@]}"
}

# Clear downloaded Colima images in current and legacy cache locations.
# VM disks, containers, and volumes live elsewhere and are retained.
function clean_colima() {
  rm -rf -- "${XDG_CACHE_HOME:-$HOME/.cache}/colima/caches" \
    "$HOME/Library/Caches/colima/caches"
}

# Quit Spotify before clearing its cache; retain application support/downloads.
function clean_spotify() {
  osascript -e 'if application "Spotify" is running then tell application "Spotify" to quit' || return
  local attempt
  for attempt in {1..30}; do
    pgrep -f '/Spotify.app/Contents/' >/dev/null || break
    sleep 1
  done
  if pgrep -f '/Spotify.app/Contents/' >/dev/null; then
    echo "Spotify is still running; quit it and retry clean_spotify." >&2
    return 1
  fi
  local cache="$HOME/Library/Caches/com.spotify.client"
  local -a entries=("$cache"/*(DN))
  (( ${#entries} )) || return 0
  rm -rf -- "${entries[@]}"
}

# Clear the shared Terraform/OpenTofu provider cache, retaining its directory.
# Projects using cached-provider symlinks may need terraform/tofu init again.
function clean_tf() {
  local cache="${XDG_CACHE_HOME:-$HOME/.cache}/terraform/plugins"
  [[ -d "$cache" ]] || return 0
  local -a entries=("$cache"/*(DN))
  (( ${#entries} )) || return 0
  rm -rf -- "${entries[@]}"
}

# Stop/remove ALL containers and clear ALL images/build cache; preserve volumes.
# Explicitly target this Mac's Colima daemon, regardless of the current context.
function clean_docker() {
  local output
  local -a containers
  output=$(docker --context colima ps -aq) || return
  containers=( ${(f)output} )
  if (( ${#containers} )); then
    docker --context colima stop "${containers[@]}" || return
    docker --context colima rm "${containers[@]}" || return
  fi
  docker --context colima builder prune --all --force || return
  docker --context colima image prune --all --force || return
  colima ssh -- sudo fstrim -av || return
  docker --context colima system df
}

# Update brew
function brew_update() {
  brew update
  brew bundle --file="$HOME/.config/brew/Brewfile" --upgrade
  brew upgrade --formula
  brew cleanup
  brew doctor
  brew missing
  brew outdated
  brew autoremove
  echo "Homebrew update complete."
}

# Save the default tmux server, then stop every tmux server owned by this user.
function tmux-restart() {
  local save_script
  save_script="$(tmux show-option -gqv '@resurrect-save-script-path' 2>/dev/null)"

  if [[ -z "$save_script" || ! -x "$save_script" ]]; then
    echo "tmux-restart: tmux-resurrect save script not found" >&2
    return 1
  fi

  "$save_script" || return
  echo "tmux state saved; stopping all tmux servers..."
  pkill -x -u "$(id -u)" tmux
}

function reset_internet() {
  sudo killall -HUP mDNSResponder && echo macOS DNS Cache Reset
  sudo pfctl -f /etc/pf.conf
  sudo ifconfig en0 down && sudo ifconfig en0 up
}

function reset_work_network() {
  tailscale set --accept-dns=false --accept-routes=false &&
    networksetup -setwebproxystate "AX88179A" off &&
    networksetup -setsecurewebproxystate "AX88179A" off
}
