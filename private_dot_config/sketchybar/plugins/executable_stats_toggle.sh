#!/bin/bash
set -euo pipefail

if [[ "$(sketchybar --query network | jq -r '.geometry.drawing')" == "on" ]]; then
  sketchybar --animate tanh 12 \
    --set network drawing=off \
    --set cpu drawing=off \
    --set gpu drawing=off \
    --set ram drawing=off \
    --set disk drawing=off
else
  sketchybar --animate tanh 12 \
    --set network drawing=on \
    --set cpu drawing=on \
    --set gpu drawing=on \
    --set ram drawing=on \
    --set disk drawing=on
fi
