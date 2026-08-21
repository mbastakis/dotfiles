#!/bin/bash
set -euo pipefail

layout="$(defaults read com.apple.HIToolbox AppleSelectedInputSources 2>/dev/null \
  | awk -F'= ' '/KeyboardLayout Name/{gsub(/[;"]/ , "", $2); print $2; exit}')"

case "$layout" in
  ABC) label="EN" ;;
  Dvorak) label="DV" ;;
  GreekDvorak | "Greek Dvorak") label="EL" ;;
  *) label="${layout:0:2}" ;;
esac

sketchybar --set "$NAME" label="$label"
