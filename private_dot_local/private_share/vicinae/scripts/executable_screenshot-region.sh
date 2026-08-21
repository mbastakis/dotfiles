#!/bin/bash
# @vicinae.schemaVersion 1
# @vicinae.title Capture Selected Portion
# @vicinae.mode silent

set -euo pipefail

nohup /usr/sbin/screencapture -ip -J selection >/dev/null 2>&1 &
