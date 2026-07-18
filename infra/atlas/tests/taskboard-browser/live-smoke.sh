#!/bin/bash
set -euo pipefail

atlas_host="${TASKBOARD_ATLAS_HOST:-atlas}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
endpoint="$(ssh "$atlas_host" 'container_id="$(sudo docker compose --project-directory /opt/homeserver -f /opt/homeserver/compose.yml ps -q taskboard)"; test -n "$container_id"; sudo docker inspect --format "{{(index .NetworkSettings.Networks \"homeserver\").IPAddress}} {{range .Config.Env}}{{if eq (index (split . \"=\") 0) \"TASKBOARD_PORT\"}}{{index (split . \"=\") 1}}{{end}}{{end}}" "$container_id"')"
read -r container_ip container_port <<<"$endpoint"
if [[ -z "$container_ip" || -z "$container_port" ]]; then
    echo "Error: Could not resolve Taskboard container endpoint" >&2
    exit 1
fi

local_port="$(python3 -c 'import socket; sock = socket.socket(); sock.bind(("127.0.0.1", 0)); print(sock.getsockname()[1]); sock.close()')"
ssh -S none -N \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=15 \
    -L "127.0.0.1:${local_port}:${container_ip}:${container_port}" \
    "$atlas_host" &
tunnel_pid=$!
trap 'kill "$tunnel_pid" 2>/dev/null || true; wait "$tunnel_pid" 2>/dev/null || true' EXIT

for _ in {1..50}; do
    if curl -fsS "http://127.0.0.1:${local_port}/healthz" >/dev/null 2>&1; then
        TASKBOARD_BASE_URL="http://127.0.0.1:${local_port}" \
            npm --prefix "$script_dir" run test:live
        exit 0
    fi
    sleep 0.1
done

echo "Error: Timed out waiting for the Taskboard SSH tunnel" >&2
exit 1
