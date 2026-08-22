#!/bin/bash
set -euo pipefail

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"
# shellcheck source=/dev/null
source "$CONFIG_DIR/colors.sh"

# Transparent variants of the resting colors, so the panel fades in place
# instead of popping.
CLEAR_SUBTEXT="${SUBTEXT_COLOR/0xff/0x00}"
CLEAR_ITEM="${ITEM_COLOR/0xff/0x00}"
CLEAR_BORDER="${BORDER_COLOR/0xff/0x00}"

stats_items=(network cpu gpu ram disk)

if [[ "$(sketchybar --query network | jq -r '.geometry.drawing')" == "on" ]]; then
  # Fade the panel out, then stop drawing it once the animation has settled.
  fade=(--animate tanh 12 --set stats icon.color="$MUTED_COLOR"
    --set stats_container background.color="$CLEAR_ITEM" background.border_color="$CLEAR_BORDER")
  for item in "${stats_items[@]}"; do
    fade+=(--set "$item" icon.color="$CLEAR_SUBTEXT" label.color="$CLEAR_SUBTEXT")
  done
  sketchybar "${fade[@]}"
  (
    sleep 0.25
    hide=(--set focused_window drawing=on
      --set stats_left_gap drawing=off
      --set stats_container drawing=off)
    for item in "${stats_items[@]}"; do
      hide+=(--set "$item" drawing=off)
    done
    sketchybar "${hide[@]}"
  ) &
else
  # Draw everything fully transparent first, then fade it in.
  show=(--set focused_window drawing=off
    --set stats_left_gap drawing=on
    --set stats_container drawing=on background.color="$CLEAR_ITEM" background.border_color="$CLEAR_BORDER")
  for item in "${stats_items[@]}"; do
    show+=(--set "$item" drawing=on icon.color="$CLEAR_SUBTEXT" label.color="$CLEAR_SUBTEXT")
  done
  sketchybar "${show[@]}"
  fade=(--animate tanh 20 --set stats icon.color="$TEXT_COLOR"
    --set stats_container background.color="$ITEM_COLOR" background.border_color="$BORDER_COLOR")
  for item in "${stats_items[@]}"; do
    fade+=(--set "$item" icon.color="$SUBTEXT_COLOR" label.color="$SUBTEXT_COLOR")
  done
  sketchybar "${fade[@]}"
fi
