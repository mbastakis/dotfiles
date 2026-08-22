#!/bin/bash
set -euo pipefail

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"
# shellcheck source=/dev/null
source "$CONFIG_DIR/colors.sh"

# Generic hover affordance for icon-only toggle items: brighten under the
# pointer, settle back to the item's resting color on exit.
case "${SENDER:-}" in
  mouse.entered)
    sketchybar --animate tanh 8 --set "$NAME" icon.color="$TEXT_COLOR"
    ;;
  mouse.exited)
    resting="$MUTED_COLOR"
    # The stats icon stays bright while the stats panel is open.
    if [[ "$NAME" == "stats" ]] \
      && [[ "$(sketchybar --query network | jq -r '.geometry.drawing')" == "on" ]]; then
      resting="$TEXT_COLOR"
    fi
    sketchybar --animate tanh 8 --set "$NAME" icon.color="$resting"
    ;;
esac
