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
	[ -n "$cwd" ] && [ "$cwd" != "$PWD" ] &&  cd -- "$cwd"
	rm -f -- "$tmp"
}

ftext() {
  rg --color=always --line-number --no-heading --smart-case "${*:-}" |
    fzf --ansi \
        --color "hl:-1:underline,hl+:-1:underline:reverse" \
        --delimiter : \
        --preview 'bat --color=always {1} --highlight-line {2}' \
        --preview-window 'up,60%,border-bottom,+{2}+3/3,~3' \
        --bind 'enter:execute(code {})';
}

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
