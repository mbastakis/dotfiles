#!/bin/bash
set -euo pipefail

macmon pipe --interval 3000 | while IFS= read -r sample; do
  gpu_usage="$(jq -r 'if .gpu_active_ratio == null then "--" else ((.gpu_active_ratio * 100) | round | tostring) + "%" end' <<<"$sample")"
  sketchybar --trigger gpu_stats "GPU_USAGE=$gpu_usage"
done
