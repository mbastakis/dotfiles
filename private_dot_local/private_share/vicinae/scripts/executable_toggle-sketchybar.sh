#!/bin/bash
# @vicinae.schemaVersion 1
# @vicinae.title SketchyBar Toggle
# @vicinae.mode silent

set -euo pipefail

sketchybar=/opt/homebrew/bin/sketchybar

if [[ "$("$sketchybar" --query bar)" == *'"hidden": "off"'* ]]; then
  "$sketchybar" --bar hidden=on
else
  "$sketchybar" --bar hidden=off
fi
