# functions.zsh - Custom shell functions

# Extract almost any archive
extract() {
  if [ -f "$1" ]; then
    case "$1" in
      *.tar.bz2)   tar xjf "$1"     ;;
      *.tar.gz)    tar xzf "$1"     ;;
      *.bz2)       bunzip2 "$1"     ;;
      *.rar)       unrar e "$1"     ;;
      *.gz)        gunzip "$1"      ;;
      *.tar)       tar xf "$1"      ;;
      *.tbz2)      tar xjf "$1"     ;;
      *.tgz)       tar xzf "$1"     ;;
      *.zip)       unzip "$1"       ;;
      *.Z)         uncompress "$1"  ;;
      *.7z)        7z x "$1"        ;;
      *)           echo "'$1' cannot be extracted via extract()" ;;
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
	mkdir $1;
	cd $1;
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
	deactivate;
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
	IFS= read -r -d '' cwd < "$tmp"
	[ -n "$cwd" ] && [ "$cwd" != "$PWD" ] && builtin cd -- "$cwd"
	rm -f -- "$tmp"
}

# =============================================================================
#
# Utility functions for zoxide.
#

# pwd based on the value of _ZO_RESOLVE_SYMLINKS.
function __zoxide_pwd() {
    \builtin pwd -L
}

# cd + custom logic based on the value of _ZO_ECHO.
function __zoxide_cd() {
    # shellcheck disable=SC2164
    \builtin cd -- "$@"
}

# =============================================================================
#
# Hook configuration for zoxide.
#

# Hook to add new entries to the database.
function __zoxide_hook() {
    # shellcheck disable=SC2312
    \command zoxide add -- "$(__zoxide_pwd)"
}

# Initialize hook.
\builtin typeset -ga precmd_functions
\builtin typeset -ga chpwd_functions
# shellcheck disable=SC2034,SC2296
precmd_functions=("${(@)precmd_functions:#__zoxide_hook}")
# shellcheck disable=SC2034,SC2296
chpwd_functions=("${(@)chpwd_functions:#__zoxide_hook}")
chpwd_functions+=(__zoxide_hook)

# Report common issues.
function __zoxide_doctor() {
    [[ ${_ZO_DOCTOR:-1} -ne 0 ]] || return 0
    [[ ${chpwd_functions[(Ie)__zoxide_hook]:-} -eq 0 ]] || return 0

    _ZO_DOCTOR=0
    \builtin printf '%s\n' \
        'zoxide: detected a possible configuration issue.' \
        'Please ensure that zoxide is initialized right at the end of your shell configuration file (usually ~/.zshrc).' \
        '' \
        'If the issue persists, consider filing an issue at:' \
        'https://github.com/ajeetdsouza/zoxide/issues' \
        '' \
        'Disable this message by setting _ZO_DOCTOR=0.' \
        '' >&2
}

# =============================================================================
#
# When using zoxide with --no-cmd, alias these internal functions as desired.
#

# Jump to a directory using only keywords.
function __zoxide_z() {
    __zoxide_doctor
    if [[ "$#" -eq 0 ]]; then
        __zoxide_cd ~
    elif [[ "$#" -eq 1 ]] && { [[ -d "$1" ]] || [[ "$1" = '-' ]] || [[ "$1" =~ ^[-+][0-9]$ ]]; }; then
        __zoxide_cd "$1"
    elif [[ "$#" -eq 2 ]] && [[ "$1" = "--" ]]; then
        __zoxide_cd "$2"
    else
        \builtin local result
        # shellcheck disable=SC2312
        result="$(\command zoxide query --exclude "$(__zoxide_pwd)" -- "$@")" && __zoxide_cd "${result}"
    fi
}

# Jump to a directory using interactive search.
function __zoxide_zi() {
    __zoxide_doctor
    \builtin local result
    result="$(\command zoxide query --interactive -- "$@")" && __zoxide_cd "${result}"
}

# =============================================================================
#
# Commands for zoxide. Disable these using --no-cmd.
#

function cd() {
    __zoxide_z "$@"
}

function cdi() {
    __zoxide_zi "$@"
}

# Completions.
if [[ -o zle ]]; then
    __zoxide_result=''

    function __zoxide_z_complete() {
        # Only show completions when the cursor is at the end of the line.
        # shellcheck disable=SC2154
        [[ "${#words[@]}" -eq "${CURRENT}" ]] || return 0

        if [[ "${#words[@]}" -eq 2 ]]; then
            # Show completions for local directories.
            _cd -/

        elif [[ "${words[-1]}" == '' ]]; then
            # Show completions for Space-Tab.
            # shellcheck disable=SC2086
            __zoxide_result="$(\command zoxide query --exclude "$(__zoxide_pwd || \builtin true)" --interactive -- ${words[2,-1]})" || __zoxide_result=''

            # Set a result to ensure completion doesn't re-run
            compadd -Q ""

            # Bind '\e[0n' to helper function.
            \builtin bindkey '\e[0n' '__zoxide_z_complete_helper'
            # Sends query device status code, which results in a '\e[0n' being sent to console input.
            \builtin printf '\e[5n'

            # Report that the completion was successful, so that we don't fall back
            # to another completion function.
            return 0
        fi
    }

    function __zoxide_z_complete_helper() {
        if [[ -n "${__zoxide_result}" ]]; then
            # shellcheck disable=SC2034,SC2296
            BUFFER="cd ${(q-)__zoxide_result}"
            __zoxide_result=''
            \builtin zle reset-prompt
            \builtin zle accept-line
        else
            \builtin zle reset-prompt
        fi
    }
    \builtin zle -N __zoxide_z_complete_helper

    [[ "${+functions[compdef]}" -ne 0 ]] && \compdef __zoxide_z_complete cd
fi

# ATUIN

# shellcheck disable=SC2034,SC2153,SC2086,SC2155

# Above line is because shellcheck doesn't support zsh, per
# https://github.com/koalaman/shellcheck/wiki/SC1071, and the ignore: param in
# ludeeus/action-shellcheck only supports _directories_, not _files_. So
# instead, we manually add any error the shellcheck step finds in the file to
# the above line ...

# Source this in your ~/.zshrc
autoload -U add-zsh-hook

zmodload zsh/datetime 2>/dev/null

# If zsh-autosuggestions is installed, configure it to use Atuin's search. If
# you'd like to override this, then add your config after the $(atuin init zsh)
# in your .zshrc
_zsh_autosuggest_strategy_atuin() {
    suggestion=$(ATUIN_QUERY="$1" atuin search --cmd-only --limit 1 --search-mode prefix)
}

if [ -n "${ZSH_AUTOSUGGEST_STRATEGY:-}" ]; then
    ZSH_AUTOSUGGEST_STRATEGY=("atuin" "${ZSH_AUTOSUGGEST_STRATEGY[@]}")
else
    ZSH_AUTOSUGGEST_STRATEGY=("atuin")
fi

export ATUIN_SESSION=$(atuin uuid)
ATUIN_HISTORY_ID=""

_atuin_preexec() {
    local id
    id=$(atuin history start -- "$1")
    export ATUIN_HISTORY_ID="$id"
    __atuin_preexec_time=${EPOCHREALTIME-}
}

_atuin_precmd() {
    local EXIT="$?" __atuin_precmd_time=${EPOCHREALTIME-}

    [[ -z "${ATUIN_HISTORY_ID:-}" ]] && return

    local duration=""
    if [[ -n $__atuin_preexec_time && -n $__atuin_precmd_time ]]; then
        printf -v duration %.0f $(((__atuin_precmd_time - __atuin_preexec_time) * 1000000000))
    fi

    (ATUIN_LOG=error atuin history end --exit $EXIT ${duration:+--duration=$duration} -- $ATUIN_HISTORY_ID &) >/dev/null 2>&1
    export ATUIN_HISTORY_ID=""
}

_atuin_search() {
    emulate -L zsh
    zle -I

    # swap stderr and stdout, so that the tui stuff works
    # TODO: not this
    local output
    # shellcheck disable=SC2048
    output=$(ATUIN_SHELL_ZSH=t ATUIN_LOG=error ATUIN_QUERY=$BUFFER atuin search $* -i 3>&1 1>&2 2>&3)

    zle reset-prompt
    # re-enable bracketed paste
    # shellcheck disable=SC2154
    echo -n ${zle_bracketed_paste[1]} >/dev/tty

    if [[ -n $output ]]; then
        RBUFFER=""
        LBUFFER=$output

        if [[ $LBUFFER == __atuin_accept__:* ]]
        then
            LBUFFER=${LBUFFER#__atuin_accept__:}
            zle accept-line
        fi
    fi
}
_atuin_search_vicmd() {
    _atuin_search --keymap-mode=vim-normal
}
_atuin_search_viins() {
    _atuin_search --keymap-mode=vim-insert
}

_atuin_up_search() {
    # Only trigger if the buffer is a single line
    if [[ ! $BUFFER == *$'\n'* ]]; then
        _atuin_search --shell-up-key-binding "$@"
    else
        zle up-line
    fi
}
_atuin_up_search_vicmd() {
    _atuin_up_search --keymap-mode=vim-normal
}
_atuin_up_search_viins() {
    _atuin_up_search --keymap-mode=vim-insert
}

add-zsh-hook preexec _atuin_preexec
add-zsh-hook precmd _atuin_precmd

zle -N atuin-search _atuin_search
zle -N atuin-search-vicmd _atuin_search_vicmd
zle -N atuin-search-viins _atuin_search_viins
zle -N atuin-up-search _atuin_up_search
zle -N atuin-up-search-vicmd _atuin_up_search_vicmd
zle -N atuin-up-search-viins _atuin_up_search_viins

# These are compatibility widget names for "atuin <= 17.2.1" users.
zle -N _atuin_search_widget _atuin_search
zle -N _atuin_up_search_widget _atuin_up_search

bindkey -M emacs '^r' atuin-search
bindkey -M viins '^r' atuin-search-viins
bindkey -M vicmd '/' atuin-search
bindkey -M emacs '^[[A' atuin-up-search
bindkey -M vicmd '^[[A' atuin-up-search-vicmd
bindkey -M viins '^[[A' atuin-up-search-viins
bindkey -M emacs '^[OA' atuin-up-search
bindkey -M vicmd '^[OA' atuin-up-search-vicmd
bindkey -M viins '^[OA' atuin-up-search-viins
bindkey -M vicmd 'k' atuin-up-search-vicmd


# Custom functions
check_repos_behind() {
    echo "Checking for repositories that are behind their remotes..."
    echo "=========================================================="
  
  behind_found=0
  
  # Find all git repositories recursively from current directory
  find . -name ".git" -type d 2>/dev/null | while read git_dir; do
    repo_dir=$(dirname "$git_dir")
    repo_path=$(realpath "$repo_dir" | sed "s|$(realpath .)||" | sed 's|^/||')
    
    # Skip if repo_path is empty (current directory)
    if [[ -z "$repo_path" ]]; then
      repo_path="."
    fi
    
    # Get current branch
    current_branch=$(git -C "$repo_dir" branch --show-current 2>/dev/null)
    if [[ -z "$current_branch" ]]; then
      continue  # Skip detached HEAD states
    fi
    
    # Fetch latest changes (quietly)
    git -C "$repo_dir" fetch --quiet 2>/dev/null
    
    # Check if remote tracking branch exists
    upstream=$(git -C "$repo_dir" rev-parse --abbrev-ref "$current_branch@{upstream}" 2>/dev/null)
    if [[ -z "$upstream" ]]; then
      continue  # Skip branches without upstream
    fi
    
    # Get behind count
    behind=$(git -C "$repo_dir" rev-list --count HEAD.."$upstream" 2>/dev/null || echo "0")
    
    # Only log if behind
    if [[ "$behind" -gt 0 ]]; then
      if [[ $behind_found -eq 0 ]]; then
        printf "%-50s %-20s %s\n" "Repository" "Branch" "Behind"
        echo "=========================================================="
        behind_found=1
      fi
      printf "%-50s %-20s %d\n" "$repo_path" "$current_branch" "$behind"
    fi
  done
  
  if [[ $behind_found -eq 0 ]]; then
    echo "✅ All repositories are up to date!"
  else
    echo "=========================================================="
    echo "⚠️  Found repositories that are behind their remotes"
    echo "Run 'git pull' in these directories to update them"
  fi
}

find_problematic_repos() {
    search_dir="${1:-$(pwd)}"

  if [[ -z "$search_dir" ]]; then
    search_dir="."
  fi
  
  if [[ ! -d "$search_dir" ]]; then
    echo "Error: Directory '$search_dir' does not exist"
    exit 1
  fi
  
  echo "Scanning for problematic repositories in: $search_dir"
  echo "=============================================="
  
  no_remote_count=0
  no_commits_count=0
  access_issue_count=0
  empty_repo_count=0
  
  # Find all git repositories recursively
  find "$search_dir" -name ".git" -type d | while read git_dir; do
    repo_dir=$(dirname "$git_dir")
    repo_path=$(realpath "$repo_dir" | sed "s|$(realpath "$search_dir")||" | sed 's|^/||')
    
    echo "Checking: $repo_path"
    
    # Check if repository has any commits
    if ! git -C "$repo_dir" rev-parse HEAD >/dev/null 2>&1; then
      echo "  🚨 PROBLEM: Repository has no commits (empty repository)"
      ((no_commits_count++))
      continue
    fi
    
    # Check if repository has any files (excluding .git)
    file_count=$(find "$repo_dir" -type f ! -path "*/.git/*" | wc -l)
    if [[ "$file_count" -eq 0 ]]; then
      echo "  🚨 PROBLEM: Repository appears empty (no files outside .git)"
      ((empty_repo_count++))
      continue
    fi
    
    # Check for remote repositories
    remotes=$(git -C "$repo_dir" remote 2>/dev/null)
    if [[ -z "$remotes" ]]; then
      echo "  ⚠️  WARNING: Repository has no remote repositories configured"
      ((no_remote_count++))
      continue
    fi
    
    # Check if we can access the remote
    remote_url=$(git -C "$repo_dir" remote get-url origin 2>/dev/null)
    if [[ -n "$remote_url" ]]; then
      # Try to fetch to test access
      if ! git -C "$repo_dir" ls-remote origin >/dev/null 2>&1; then
        echo "  🚨 PROBLEM: Cannot access remote repository (access denied or network issue)"
        echo "    Remote URL: $remote_url"
        ((access_issue_count++))
        continue
      fi
    fi
    
    echo "  ✅ Repository appears healthy"
  done
  
  echo "=============================================="
  echo "Problem Summary:"
  echo "  🚨 Empty repositories (no commits): $no_commits_count"
  echo "  🚨 Empty repositories (no files): $empty_repo_count"
  echo "  🚨 Access issues: $access_issue_count"
  echo "  ⚠️  No remotes configured: $no_remote_count"
  
  total_problems=$((no_commits_count + empty_repo_count + access_issue_count))
  if [[ $total_problems -eq 0 ]]; then
    echo ""
    echo "🎉 No serious problems found! All repositories appear healthy."
  else
    echo ""
    echo "💡 Recommendations:"
    if [[ $no_commits_count -gt 0 ]]; then
      echo "  - Empty repositories with no commits can likely be deleted"
    fi
    if [[ $empty_repo_count -gt 0 ]]; then
      echo "  - Empty repositories with no files may need initialization or deletion"
    fi
    if [[ $access_issue_count -gt 0 ]]; then
      echo "  - Check network connectivity and access permissions for repositories with access issues"
    fi
    if [[ $no_remote_count -gt 0 ]]; then
      echo "  - Consider adding remote repositories for local-only repos if needed"
    fi
  fi
}
