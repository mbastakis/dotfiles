#!/bin/bash
set -euo pipefail

CONFIG_DIR="${CONFIG_DIR:-$HOME/.config/sketchybar}"
CACHE_DIR="$HOME/.cache/sketchybar"
CALENDAR_IMAGE="$CACHE_DIR/calendar.png"
CALENDAR_STAMP="$CACHE_DIR/calendar-date"

# shellcheck source=/dev/null
source "$CONFIG_DIR/colors.sh"
: "${TEXT_COLOR:?}" "${SUBTEXT_COLOR:?}" "${ACCENT_COLOR:?}" "${ACTIVE_TEXT_COLOR:?}"

sketchybar --set clock label="$(date '+%H:%M')"

mkdir -p "$CACHE_DIR"
today="$(date '+%Y-%m-%d')"
render_version=4
if [[ -f "$CALENDAR_IMAGE" && "$(cat "$CALENDAR_STAMP" 2>/dev/null || true)" == "$today:$render_version" ]]; then
  sketchybar --set calendar background.image="$CALENDAR_IMAGE"
  exit 0
fi

hex_color() {
  printf '#%s' "${1:4}"
}

text_color="$(hex_color "$TEXT_COLOR")"
subtext_color="$(hex_color "$SUBTEXT_COLOR")"
accent_color="$(hex_color "$ACCENT_COLOR")"
active_text_color="$(hex_color "$ACTIVE_TEXT_COLOR")"
month_label="$(date '+%B %Y')"
font_file="$(fc-match 'JetBrainsMono Nerd Font Mono' -f '%{file}' | head -1)"
current_day="$((10#$(date '+%d')))"
first_weekday="$(date -j -f '%Y-%m-%d' "$(date '+%Y-%m')-01" '+%w')"
days_in_month="$((10#$(date -j -v1d -v+1m -v-1d '+%d')))"

# Render at Retina resolution, then let SketchyBar display it at 280x300 points.
command=(magick -size 560x600 xc:none -font "$font_file")
command+=(
  -fill "$text_color" -pointsize 42 -gravity north
  -annotate +0+38 "$month_label"
  -fill "$subtext_color" -pointsize 26
)

weekdays=(Su Mo Tu We Th Fr Sa)
for column in "${!weekdays[@]}"; do
  x="$((56 + (column * 74)))"
  command+=( -gravity northwest -annotate "+$x+144" "${weekdays[$column]}" )
done

for ((day = 1; day <= days_in_month; day++)); do
  cell="$((first_weekday + day - 1))"
  column="$((cell % 7))"
  row="$((cell / 7))"
  x="$((74 + (column * 74)))"
  y="$((234 + (row * 68)))"

  if ((day == current_day)); then
    command+=(
      -fill "$accent_color"
      -draw "roundrectangle $((x - 29)),$((y - 37)) $((x + 29)),$((y + 21)) 15,15"
      -fill "$active_text_color"
    )
  else
    command+=( -fill "$text_color" )
  fi

  text_offset="$(printf '%+d%+d' "$((x - 280))" "$((y - 300 - 8))")"
  command+=(
    -pointsize 31
    -gravity center
    -annotate "$text_offset" "$day"
  )
done

"${command[@]}" -define png:color-type=6 "$CALENDAR_IMAGE"
printf '%s:%s\n' "$today" "$render_version" > "$CALENDAR_STAMP"
sketchybar --set calendar background.image="$CALENDAR_IMAGE"
