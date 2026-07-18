#!/bin/bash
set -euo pipefail

TASKBOARD_CONFIG="${TASKBOARD_CONFIG:-/config}"
TASKBOARD_DATA="${TASKBOARD_DATA:-/data}"
TASKBOARD_PORT="${TASKBOARD_PORT:-8080}"
TASKBOARD_USERNAME="${TASKBOARD_USERNAME:-mbastakis}"
TASK_SYNC_SERVER_URL="${TASK_SYNC_SERVER_URL:-http://taskchampion-sync:8080}"
TASK_SYNC_CLIENT_ID="${TASK_SYNC_CLIENT_ID:-24e1b420-97ae-4847-9fae-cf15c096706b}"
TASKBOARD_DONE_DAYS="${TASKBOARD_DONE_DAYS:-14}"

if [[ -z "${TASK_SYNC_ENCRYPTION_SECRET:-}" ]]; then
    printf '%s\n' "TASK_SYNC_ENCRYPTION_SECRET is required" >&2
    exit 1
fi

if [[ -z "${TASKBOARD_PASSWORD:-}" && "${TASKBOARD_ALLOW_NO_AUTH:-}" != "1" ]]; then
    printf '%s\n' "TASKBOARD_PASSWORD is required unless TASKBOARD_ALLOW_NO_AUTH=1" >&2
    exit 1
fi

mkdir -p "$TASKBOARD_CONFIG" "$TASKBOARD_DATA"
umask 077

cat >"$TASKBOARD_CONFIG/taskrc" <<EOF
# Generated at container startup.
data.location=$TASKBOARD_DATA
confirmation=no
verbose=default,-override
color=off
detection=on
dateformat=Y-M-D
dateformat.edit=Y-M-D H:N:S
weekstart=Monday
sync.server.url=$TASK_SYNC_SERVER_URL
sync.server.client_id=$TASK_SYNC_CLIENT_ID
sync.encryption_secret=$TASK_SYNC_ENCRYPTION_SECRET
EOF

export TASKRC="$TASKBOARD_CONFIG/taskrc"
export TASKDATA="$TASKBOARD_DATA"
export TASKBOARD_CONFIG
export TASKBOARD_DATA
export TASKBOARD_PORT
export TASKBOARD_USERNAME
export TASKBOARD_DONE_DAYS

exec python3 /app/taskboard.py
