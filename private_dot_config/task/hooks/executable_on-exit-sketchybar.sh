#!/bin/bash
# Taskwarrior on-exit hook: tell SketchyBar that task data may have changed.
# Detached so `task` never waits on the bar; silent when the bar is absent.
sketchybar_bin="$(command -v sketchybar 2>/dev/null || echo /opt/homebrew/bin/sketchybar)"
if [[ -x "$sketchybar_bin" ]]; then
  ("$sketchybar_bin" --trigger task_change >/dev/null 2>&1 &)
fi
exit 0
