#!/bin/bash
set -euo pipefail

exec "$(dirname "$0")/vpn_menu.sh" WireGuard
