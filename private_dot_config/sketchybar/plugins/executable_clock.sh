#!/bin/bash
set -euo pipefail

sketchybar --set "$NAME" label="$(date '+%d/%m/%Y %H:%M')"
