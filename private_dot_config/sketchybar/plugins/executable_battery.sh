#!/bin/bash
set -euo pipefail

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"
# shellcheck source=/dev/null
source "$CONFIG_DIR/colors.sh"

battery_status="$(pmset -g batt)"
percentage="$(sed -n 's/.*[[:space:]]\([0-9][0-9]*\)%.*/\1/p' <<<"$battery_status")"

if [[ -z "$percentage" ]]; then
  sketchybar --set "$NAME" drawing=off
  exit 0
fi

case "$percentage" in
  100) icon="󰁹" ;;
  9[0-9]) icon="󰂂" ;;
  8[0-9]) icon="󰂁" ;;
  7[0-9]) icon="󰂀" ;;
  6[0-9]) icon="󰁿" ;;
  5[0-9]) icon="󰁾" ;;
  4[0-9]) icon="󰁽" ;;
  3[0-9]) icon="󰁼" ;;
  2[0-9]) icon="󰁻" ;;
  1[0-9]) icon="󰁺" ;;
  *) icon="󰂎" ;;
esac

# Quiet at rest; the pill + colored border are reserved for states that
# deserve attention (low, critical, charging).
color="$SUBTEXT_COLOR"
pill=off
border_width=0
# shellcheck disable=SC2153 # Provided by colors.sh.
border_color="$BORDER_COLOR"
if (( percentage <= 10 )); then
  color="$ERROR_COLOR"
  pill=on
  border_width=1
  border_color="$ERROR_COLOR"
elif (( percentage <= 25 )); then
  color="$WARNING_COLOR"
  pill=on
  border_width=1
  border_color="$WARNING_COLOR"
fi

if grep -qE 'AC Power|charging|charged' <<<"$battery_status"; then
  icon="󰂄"
  color="$INFO_COLOR"
  pill=on
  border_width=1
  border_color="$INFO_COLOR"
fi

sketchybar --animate tanh 12 --set "$NAME" \
  drawing=on \
  icon="$icon" \
  icon.color="$color" \
  label="${percentage}%" \
  label.color="$TEXT_COLOR" \
  background.drawing="$pill" \
  background.border_width="$border_width" \
  background.border_color="$border_color"
