#!/usr/bin/env zsh
# tools.zsh - Tool initializations and shell integrations
# Note: Atuin is loaded in fzf.zsh (after fzf) so it can bind Ctrl+R

# Mise - runtime tool activation
if command -v mise &>/dev/null; then
    eval "$(mise activate zsh)"

    # Mise's own completion can be cached as a normal fpath function.
    if [[ -n "${ZSH_COMPLETION_DIR:-}" ]]; then
        _mise_completion="$ZSH_COMPLETION_DIR/_mise"
        _mise_tmp="$_mise_completion.tmp"
        _mise_bin="$(command -v mise)"

        if [[ ! -s "$_mise_completion" || "$_mise_bin" -nt "$_mise_completion" ]]; then
            if mise completion zsh >|"$_mise_tmp" 2>/dev/null; then
                mv "$_mise_tmp" "$_mise_completion"
            else
                rm -f "$_mise_tmp"
            fi
        fi

        [[ -s "$_mise_completion" ]] && source "$_mise_completion"
        unset _mise_completion _mise_tmp _mise_bin
    fi

    # go-task uses the same `task` command name as Taskwarrior. Enable its
    # completion only while mise currently resolves `task` to go-task.
    if [[ -n "${ZSH_COMPLETION_CACHE_DIR:-}" ]]; then
        _mise_cache_go_task_completion() {
            local _task_bin="${1:-}"
            local _completion="$ZSH_COMPLETION_CACHE_DIR/go-task-completion.zsh"
            local _meta="$_completion.meta"
            local _tmp="$_completion.tmp"
            local _state

            mkdir -p "$ZSH_COMPLETION_CACHE_DIR"

            if [[ -n "$_task_bin" ]]; then
                _state="task-bin=$_task_bin"
            elif [[ -n "${DOTFILES_PATH:-}" && -f "$DOTFILES_PATH/mise.toml" ]]; then
                _state="dotfiles-mise=$DOTFILES_PATH/mise.toml"
            else
                _state="mise-exec-default"
            fi

            if [[ -s "$_completion" && -f "$_meta" && "$_state" == "$(<"$_meta")" ]]; then
                return 0
            fi

            if [[ -n "$_task_bin" ]]; then
                task --completion zsh >|"$_tmp" 2>/dev/null || {
                    rm -f "$_tmp"
                    return 1
                }
            elif [[ -n "${DOTFILES_PATH:-}" && -f "$DOTFILES_PATH/mise.toml" ]]; then
                (cd "$DOTFILES_PATH" && mise exec -- task --completion zsh) >|"$_tmp" 2>/dev/null || {
                    rm -f "$_tmp"
                    return 1
                }
            else
                mise exec -- task --completion zsh >|"$_tmp" 2>/dev/null || {
                    rm -f "$_tmp"
                    return 1
                }
            fi

            mv "$_tmp" "$_completion"
            print -r -- "$_state" >|"$_meta"
        }

        _mise_task_completion_hook() {
            local _task_bin _mise_data_dir _completion

            hash -r 2>/dev/null || true
            _task_bin="$(command -v task 2>/dev/null || true)"
            _mise_data_dir="${MISE_DATA_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/mise}"
            _completion="$ZSH_COMPLETION_CACHE_DIR/go-task-completion.zsh"

            if [[ "$_task_bin" == "$_mise_data_dir/installs/task/"* ]]; then
                _mise_cache_go_task_completion "$_task_bin" || return 0
                if [[ "${_MISE_TASK_COMPLETION_ACTIVE:-}" != "$_task_bin" ]]; then
                    source "$_completion"
                    _MISE_TASK_COMPLETION_ACTIVE="$_task_bin"
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
fi

# Normalize XDG tool bins after PATH mutators like mise.
path=(${path:#$HOME/.cargo/bin})
path=(${path:#$HOME/.bun/bin})
[[ -d "$CARGO_HOME/bin" ]] && path=("$CARGO_HOME/bin" ${path:#$CARGO_HOME/bin})
[[ -d "$BUN_INSTALL/bin" ]] && path=("$BUN_INSTALL/bin" ${path:#$BUN_INSTALL/bin})

# Zoxide - smart cd
if command -v zoxide &>/dev/null; then
    # Unalias zi if it exists (conflicts with zinit)
    (( ${+aliases[zi]} )) && unalias zi
    # _ZO_FZF_OPTS is defined in fzf.zsh
    eval "$(zoxide init --cmd cd zsh)"
fi

# Direnv - per-directory environment
command -v direnv &>/dev/null && eval "$(direnv hook zsh)"

# Starship - prompt
command -v starship &>/dev/null && eval "$(starship init zsh)"

# aws-login - shell integration + agent skills
if command -v aws-login &>/dev/null; then
    eval "$(aws-login init zsh)"
    [[ ! -f ~/.config/opencode/skills/aws-login/SKILL.md ]] && aws-login skills install opencode &>/dev/null
fi
