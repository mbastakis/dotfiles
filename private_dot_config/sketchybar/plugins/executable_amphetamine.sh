#!/bin/bash
set -euo pipefail

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"
# shellcheck source=/dev/null
source "$CONFIG_DIR/colors.sh"

update_item() {
  local active remaining label

  active="$(/usr/bin/osascript -e 'tell application "Amphetamine" to return session is active' 2>/dev/null || echo false)"
  if [[ "$active" != "true" ]]; then
    sketchybar --animate tanh 12 --set amphetamine \
      icon.color="$MUTED_COLOR" \
      label.drawing=off \
      background.drawing=off \
      background.border_width=0
    return
  fi

  remaining="$(/usr/bin/osascript -e 'tell application "Amphetamine" to return session time remaining' 2>/dev/null || echo 0)"
  case "$remaining" in
    0) label="∞" ;;
    -1) label="trigger" ;;
    -2) label="active" ;;
    *)
      if (( remaining >= 3600 )); then
        label="$((remaining / 3600))h $(((remaining % 3600) / 60))m"
      else
        label="$((remaining / 60))m"
      fi
      ;;
  esac

  sketchybar --animate tanh 12 --set amphetamine \
    icon.color="$WARNING_COLOR" \
    label.drawing=on \
    label="$label" \
    label.color="$TEXT_COLOR" \
    background.drawing=on \
    background.border_width=1 \
    background.border_color="$WARNING_COLOR"
}

case "${1:-update}" in
  click)
    if [[ "${BUTTON:-left}" == "right" ]]; then
      /usr/bin/open -a Amphetamine
    elif [[ "$(/usr/bin/osascript -e 'tell application "Amphetamine" to return session is active')" == "true" ]]; then
      /usr/bin/osascript -e 'tell application "Amphetamine" to end session' >/dev/null
      update_item
    else
      /usr/bin/osascript -e 'tell application "Amphetamine" to start new session' >/dev/null
      update_item
    fi
    ;;
  update)
    update_item
    ;;
  *)
    echo "Usage: $0 {click|update}" >&2
    exit 2
    ;;
esac
