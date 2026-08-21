#!/bin/bash
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

DISPLAY_NAME="LC49G95T"
NATIVE_MODE=204
SCALED_MODE=79

command -v betterdisplaycli &>/dev/null || {
  sketchybar --set "$NAME" label="N/A"
  exit 0
}

current_mode="$(betterdisplaycli get -namelike="$DISPLAY_NAME" -displaymodenumber 2>/dev/null || true)"

if [[ "${1:-}" == "toggle" ]]; then
  if [[ "$current_mode" == "$NATIVE_MODE" ]]; then
    target_mode="$SCALED_MODE"
  else
    target_mode="$NATIVE_MODE"
  fi

  betterdisplaycli set -namelike="$DISPLAY_NAME" -displaymodenumber="$target_mode" >/dev/null
  sleep 1
  current_mode="$(betterdisplaycli get -namelike="$DISPLAY_NAME" -displaymodenumber 2>/dev/null || true)"
fi

case "$current_mode" in
  "$NATIVE_MODE") label="Ultrawide" ;;
  "$SCALED_MODE") label="Normal" ;;
  *)
    resolution="$(betterdisplaycli get -namelike="$DISPLAY_NAME" -resolution 2>/dev/null || true)"
    label="${resolution%%x*}"
    [[ -n "$label" ]] || label="N/A"
    ;;
esac

sketchybar --set "$NAME" label="$label"
