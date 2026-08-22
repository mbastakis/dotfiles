#!/bin/bash
set -euo pipefail

app_name="${1:?Usage: vpn_menu.sh APP_NAME [PROCESS_NAME]}"
process_name="${2:-$app_name}"

if ! pgrep -x "$process_name" >/dev/null; then
    open -gja "$app_name"
    for _ in {1..20}; do
        pgrep -x "$process_name" >/dev/null && break
        sleep 0.1
    done
fi

osascript - "$process_name" <<'APPLESCRIPT'
on run arguments
    set processName to item 1 of arguments

    tell application "System Events"
        if not (exists process processName) then error processName & " process was not found"

        tell process processName
            repeat with appMenuBar in menu bars
                repeat with appMenuItem in menu bar items of appMenuBar
                    try
                        if description of appMenuItem is "status menu" then
                            click appMenuItem
                            return
                        end if
                    end try
                end repeat
            end repeat
        end tell
    end tell

    error processName & " status menu was not found"
end run
APPLESCRIPT
