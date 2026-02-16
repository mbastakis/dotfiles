#!/bin/bash
set -euo pipefail

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Qwerty
# @raycast.mode inline

# Optional parameters:
# @raycast.packageName Keyboard Layout
# @raycast.description Switch input source to ABC (Qwerty)

"$HOME/bin/switch-input-source" --to qwerty
