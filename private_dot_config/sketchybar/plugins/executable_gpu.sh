#!/bin/bash
set -euo pipefail

sketchybar --set "$NAME" label="GPU ${GPU_USAGE:---}"
