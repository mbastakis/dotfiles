#!/usr/bin/env zsh
# completions.zsh - Tool-specific completions

# Cache generated completion output until each binary changes.
_generate_completion_cache() {
  local cache_file="$1" binary="$2"
  shift 2
  local tmp_file="$cache_file.tmp.$$"

  if [[ ! -s "$cache_file" || "$binary" -nt "$cache_file" ]]; then
    if "$@" >|"$tmp_file" 2>/dev/null; then
      mv "$tmp_file" "$cache_file"
    else
      rm -f "$tmp_file"
    fi
  fi

  [[ -s "$cache_file" ]] && source "$cache_file"
}

if command -v mise &>/dev/null; then
  _generate_completion_cache "$ZSH_COMPLETION_CACHE_DIR/mise-completion.zsh" "$(command -v mise)" mise completion zsh
fi

# go-task shares the `task` name with Taskwarrior. Generate through mise when
# necessary, then keep the compdef synchronized with whichever command wins PATH.
if command -v mise &>/dev/null; then
  _mise_cache_go_task_completion() {
    local task_bin="${1:-}"
    local completion="$ZSH_COMPLETION_CACHE_DIR/go-task-completion.zsh"
    local meta="$completion.meta"
    local tmp="$completion.tmp"
    local state

    if [[ -n "$task_bin" ]]; then
      state="task-bin=$task_bin"
    elif [[ -n "${DOTFILES_PATH:-}" && -f "$DOTFILES_PATH/mise.toml" ]]; then
      state="dotfiles-mise=$DOTFILES_PATH/mise.toml"
    else
      state="mise-exec-default"
    fi

    if [[ -s "$completion" && -f "$meta" && "$state" == "$(<"$meta")" ]]; then
      return 0
    fi

    if [[ -n "$task_bin" ]]; then
      task --completion zsh >|"$tmp" 2>/dev/null || {
        rm -f "$tmp"
        return 1
      }
    elif [[ -n "${DOTFILES_PATH:-}" && -f "$DOTFILES_PATH/mise.toml" ]]; then
      (cd "$DOTFILES_PATH" && mise exec -- task --completion zsh) >|"$tmp" 2>/dev/null || {
        rm -f "$tmp"
        return 1
      }
    else
      mise exec -- task --completion zsh >|"$tmp" 2>/dev/null || {
        rm -f "$tmp"
        return 1
      }
    fi

    mv "$tmp" "$completion"
    print -r -- "$state" >|"$meta"
  }

  _mise_task_completion_hook() {
    local task_bin mise_data_dir completion

    hash -r 2>/dev/null || true
    task_bin="$(command -v task 2>/dev/null || true)"
    mise_data_dir="${MISE_DATA_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/mise}"
    completion="$ZSH_COMPLETION_CACHE_DIR/go-task-completion.zsh"

    if [[ "$task_bin" == "$mise_data_dir/installs/task/"* ]]; then
      _mise_cache_go_task_completion "$task_bin" || return 0
      if [[ "${_MISE_TASK_COMPLETION_ACTIVE:-}" != "$task_bin" ]]; then
        source "$completion"
        _MISE_TASK_COMPLETION_ACTIVE="$task_bin"
      fi
      compdef _task task 2>/dev/null
    else
      _MISE_TASK_COMPLETION_ACTIVE=""
      compdef -d task 2>/dev/null
    fi
  }

  _mise_cache_go_task_completion
  autoload -Uz add-zsh-hook
  add-zsh-hook -d precmd _mise_task_completion_hook 2>/dev/null
  add-zsh-hook -d chpwd _mise_task_completion_hook 2>/dev/null
  add-zsh-hook precmd _mise_task_completion_hook
  add-zsh-hook chpwd _mise_task_completion_hook
  _mise_task_completion_hook
fi

# AWS CLI ships a bash completer; register it through bashcompinit.
if command -v aws_completer &>/dev/null; then
  autoload -Uz bashcompinit
  bashcompinit
  complete -C "$(command -v aws_completer)" aws
fi

# Cache OpenCode's native completion output until the binary changes.
if command -v opencode &>/dev/null; then
  _generate_completion_cache "$ZSH_COMPLETION_CACHE_DIR/opencode-completion.zsh" "$(command -v opencode)" opencode completion
fi

# Cache sesh's native completion output until the binary changes.
if command -v sesh &>/dev/null; then
  _generate_completion_cache "$ZSH_COMPLETION_CACHE_DIR/sesh-completion.zsh" "$(command -v sesh)" sesh completion zsh
fi

unset -f _generate_completion_cache
