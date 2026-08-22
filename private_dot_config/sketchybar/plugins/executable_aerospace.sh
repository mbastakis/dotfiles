#!/bin/bash
set -euo pipefail

workspace_id="${1:?workspace identifier required}"
focused_workspace="${FOCUSED_WORKSPACE:-}"
CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"

# shellcheck source=/dev/null
source "$CONFIG_DIR/colors.sh"

# Hover affordance: unfocused letters brighten with a faint chip under the
# pointer; the focused workspace already wears its full chip and stays put.
case "${SENDER:-}" in
  mouse.entered)
    if [[ "$workspace_id" != "$focused_workspace" ]]; then
      sketchybar --animate tanh 8 --set "$NAME" \
        label.color="$TEXT_COLOR" \
        background.color="$ACCENT_CHIP_HOVER"
    fi
    exit 0
    ;;
  mouse.exited)
    if [[ "$workspace_id" != "$focused_workspace" ]]; then
      sketchybar --animate tanh 8 --set "$NAME" \
        label.color="$SUBTEXT_COLOR" \
        background.color="$ACCENT_CHIP_OFF"
    fi
    exit 0
    ;;
esac

# Active workspace gets two cues: rose label plus a subtle rose chip, so the
# state survives color-only ambiguity. The chip is always drawn and fades via
# alpha, so switching workspaces cross-fades instead of snapping.
if [[ "$workspace_id" == "$focused_workspace" ]]; then
  sketchybar --animate tanh 16 --set "$NAME" \
    label.color="$ACCENT_COLOR" \
    background.color="$ACCENT_CHIP"
else
  sketchybar --animate tanh 16 --set "$NAME" \
    label.color="$SUBTEXT_COLOR" \
    background.color="$ACCENT_CHIP_OFF"
fi
