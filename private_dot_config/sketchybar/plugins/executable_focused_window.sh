#!/bin/bash
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

window_id="${WINDOW_ID:-}"
if [[ -z "$window_id" ]] && command -v aerospace &>/dev/null; then
  window_id="$(aerospace list-windows --focused --format '%{window-id}' 2>/dev/null || true)"
fi

if [[ -z "$window_id" ]]; then
  sketchybar --set "$NAME" drawing=off
  exit 0
fi

window="$(aerospace echo --window-id "$window_id" -- $'%{app-name}\t%{window-title}' 2>/dev/null || true)"
app="${window%%$'\t'*}"
title="${window#*$'\t'}"

# Strip emoji and pictographs from titles: the bar's iconography is
# monochrome Nerd Font glyphs, and a color emoji becomes an accidental
# focal point.
strip_emoji() {
  LC_ALL=en_US.UTF-8 perl -CS -pe '
    s/[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}\x{FE00}-\x{FE0F}\x{200D}]//g;
    s/\s{2,}/ /g; s/^\s+|\s+$//g; s/\s*[·—-]\s*$//;
  ' 2>/dev/null <<<"$1" || printf '%s' "$1"
}
title="$(strip_emoji "$title")"

if [[ -z "$app" ]]; then
  sketchybar --set "$NAME" drawing=off
  exit 0
fi

if [[ -z "$title" || "$title" == "$app" ]]; then
  label="$app"
else
  label="$app · $title"
fi

sketchybar --set "$NAME" drawing=on icon.background.image="app.$app" label="$label"
