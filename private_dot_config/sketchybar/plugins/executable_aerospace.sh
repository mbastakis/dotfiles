#!/bin/bash
set -euo pipefail

workspace_id="${1:?workspace identifier required}"
focused_workspace="${FOCUSED_WORKSPACE:-}"

if [[ "$workspace_id" == "$focused_workspace" ]]; then
  sketchybar --set "$NAME" \
    label.color=0xff11111b \
    background.color=0xff89b4fa
else
  sketchybar --set "$NAME" \
    label.color=0xffa6adc8 \
    background.color=0xff313244
fi
