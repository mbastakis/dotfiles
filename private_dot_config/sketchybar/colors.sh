# shellcheck shell=bash disable=SC2034
# Variables are sourced by SketchyBar and read by its Lua color loader.
# Nocturne Rose native SketchyBar colors (nocturne-rose).
# Structure
BAR_COLOR=0xf0121217
ITEM_COLOR=0xff18181f
BORDER_COLOR=0xff30303d
SURFACE_COLOR=0xff22222c
# Text hierarchy mirrors the palette tiers: TEXT (primary) > SUBTEXT
# (secondary) > MUTED (resting toggles)
TEXT_COLOR=0xffebe7ed
SUBTEXT_COLOR=0xffaaa5b0
MUTED_COLOR=0xff77727f
ACTIVE_TEXT_COLOR=0xff09090b
# Semantic
ACCENT_COLOR=0xffd48aa4
ACCENT_CHIP=0x2ed48aa4
ACCENT_CHIP_HOVER=0x14d48aa4
ACCENT_CHIP_OFF=0x00d48aa4
SUCCESS_COLOR=0xff8aa47f
WARNING_COLOR=0xffd3b069
ERROR_COLOR=0xffcc655c
INFO_COLOR=0xff88a8bd
# Legacy aliases (kept for compatibility)
BLUE="$INFO_COLOR"
MAUVE=0xffb69acb
GREEN="$SUCCESS_COLOR"
PEACH="$WARNING_COLOR"
