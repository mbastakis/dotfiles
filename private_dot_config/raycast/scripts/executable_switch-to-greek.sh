#!/bin/bash
set -euo pipefail

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Greek
# @raycast.mode inline

# Optional parameters:
# @raycast.packageName Keyboard Layout
# @raycast.description Switch input source to Greek Dvorak

"$HOME/bin/switch-input-source" --to greek
