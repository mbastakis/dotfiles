#!/bin/bash
set -euo pipefail

session="theme-showcase"
repo_root=$(git rev-parse --show-toplevel)
assets_dir="$repo_root/docs/assets/theme"
tmp_root=$(mktemp -d "${TMPDIR%/}/theme-showcase.XXXXXX")
demo_dir="$tmp_root/nocturne-demo"
ghostty_pid=""
showcase_client=""
hidden_ghostty_pids=()

cleanup() {
    tmux kill-session -t "$session" 2>/dev/null || true
    if [[ -n "$ghostty_pid" ]]; then
        kill "$ghostty_pid" 2>/dev/null || true
    fi
    for pid in "${hidden_ghostty_pids[@]}"; do
        osascript -e "tell application \"System Events\" to set visible of first process whose unix id is $pid to true" 2>/dev/null || true
    done
    rm -rf "$tmp_root"
}
trap cleanup EXIT

for command in cwebp ghostty lazygit opencode2 osascript screencapture sketchybar tmux; do
    if ! command -v "$command" &>/dev/null; then
        echo "Error: $command is required" >&2
        exit 1
    fi
done

if ! pgrep -x sketchybar &>/dev/null; then
    echo "Error: SketchyBar must be running" >&2
    exit 1
fi

mkdir -p "$assets_dir" "$demo_dir/app" "$demo_dir/docs"

cat > "$demo_dir/app/dashboard.lua" <<'EOF'
local M = {}

local services = {
    { name = "editor", state = "ready" },
    { name = "terminal", state = "ready" },
    { name = "preview", state = "review" },
}

function M.summary()
    return vim.tbl_map(function(service)
        return string.format("%-10s %s", service.name, service.state)
    end, services)
end

return M
EOF

cat > "$demo_dir/app/palette.lua" <<'EOF'
return {
    background = "base",
    foreground = "text",
    focus = "rose",
    success = "green",
    warning = "amber",
    error = "red",
}
EOF

cat > "$demo_dir/docs/README.md" <<'EOF'
# Nocturne Demo

A synthetic repository used to capture the current workstation theme.

- Ghostty and tmux provide the terminal frame.
- LazyGit shows repository navigation and diffs.
- OpenCode shows the active agent interface and session sidebar.
EOF

cat > "$demo_dir/README.md" <<'EOF'
# Nocturne Rose

A publish-safe workspace for the theme showcase.
EOF

cat > "$demo_dir/.gitignore" <<'EOF'
.cache/
EOF

(
    cd "$demo_dir"
    git init -q
    git config user.name "Theme Showcase"
    git config user.email "showcase@example.invalid"
    git add .
    GIT_AUTHOR_DATE="2026-08-20T18:00:00Z" \
        GIT_COMMITTER_DATE="2026-08-20T18:00:00Z" \
        git commit -qm "feat: create themed workspace"

    printf '\n## Design note\n\nRose marks focus while semantic colors retain meaning.\n' >> README.md
    git add README.md
    GIT_AUTHOR_DATE="2026-08-21T18:00:00Z" \
        GIT_COMMITTER_DATE="2026-08-21T18:00:00Z" \
        git commit -qm "docs: explain palette contract"

    perl -0pi -e 's/state = "review"/state = "ready"/' app/dashboard.lua
)

tmux has-session -t "$session" 2>/dev/null && tmux kill-session -t "$session"
tmux new-session -d -s "$session" -n workspace -c "$demo_dir" "lazygit"
tmux split-window -h -p 32 -t "$session:1" -c "$demo_dir" \
    "git --no-pager diff --color=always; printf '\n'; git --no-pager log --oneline --decorate -4; while :; do sleep 3600; done"
tmux select-pane -t "$session:1.1"
tmux new-window -t "$session:2" -n opencode -c "$demo_dir" \
    "opencode2 --auto '$demo_dir'"
tmux select-window -t "$session:1"

existing_pids=$(pgrep -x ghostty | tr '\n' ' ' || true)
existing_clients=$(tmux list-clients -F '#{client_tty}' | tr '\n' ' ' || true)
open -na Ghostty.app --args --config-file="$HOME/.config/ghostty/config"

for _ in {1..30}; do
    for pid in $(pgrep -x ghostty); do
        if [[ " $existing_pids " != *" $pid "* ]]; then
            ghostty_pid="$pid"
            break 2
        fi
    done
    sleep 1
done

if [[ -z "$ghostty_pid" ]]; then
    echo "Error: could not identify the showcase Ghostty process" >&2
    exit 1
fi

for pid in $existing_pids; do
    osascript -e "tell application \"System Events\" to set visible of first process whose unix id is $pid to false"
    hidden_ghostty_pids+=("$pid")
done

for _ in {1..30}; do
    while IFS= read -r client; do
        [[ -z "$client" ]] && continue
        if [[ " $existing_clients " != *" $client "* ]]; then
            showcase_client="$client"
            break 2
        fi
    done < <(tmux list-clients -F '#{client_tty}')
    sleep 1
done

if [[ -z "$showcase_client" ]]; then
    echo "Error: could not identify the showcase tmux client" >&2
    exit 1
fi

tmux switch-client -c "$showcase_client" -t "$session"

osascript <<EOF
tell application "System Events"
    tell first process whose unix id is $ghostty_pid
        set frontmost to true
        set position of front window to {40, 54}
        set size of front window to {1648, 1013}
    end tell
end tell
EOF

sleep 3
screencapture -x -R 0,0,1728,1117 "$tmp_root/terminal-workspace.png"
cwebp -quiet -lossless -m 6 "$tmp_root/terminal-workspace.png" \
    -o "$assets_dir/terminal-workspace.webp"

tmux select-window -t "$session:2"

for _ in {1..60}; do
    pane_text=$(tmux capture-pane -p -t "$session:2.1" -S -40 2>/dev/null || true)
    if [[ "$pane_text" == *"ctrl+p commands"* ]]; then
        break
    fi
    sleep 1
done

tmux send-keys -t "$session:2.1" \
    "Inspect this small demo repository and summarize its theme architecture in three concise bullets. Do not modify files." Enter

response_started=false
response_finished=false
for _ in {1..120}; do
    pane_text=$(tmux capture-pane -p -t "$session:2.1" -S -120 2>/dev/null || true)
    if [[ "$pane_text" == *"esc interrupt"* ]]; then
        response_started=true
    elif [[ "$response_started" == true ]]; then
        response_finished=true
        break
    fi
    sleep 1
done

if [[ "$response_finished" != true ]]; then
    echo "Error: OpenCode did not finish the showcase response" >&2
    exit 1
fi

sleep 2
# The configured OpenCode leader is Ctrl-X; leader+b opens the session sidebar.
tmux send-keys -t "$session:2.1" C-x b
sleep 3
screencapture -x -R 0,0,1728,1117 "$tmp_root/opencode-session.png"
cwebp -quiet -lossless -m 6 "$tmp_root/opencode-session.png" \
    -o "$assets_dir/opencode-session.webp"

printf 'Updated:\n  %s\n  %s\n' \
    "$assets_dir/terminal-workspace.webp" \
    "$assets_dir/opencode-session.webp"
