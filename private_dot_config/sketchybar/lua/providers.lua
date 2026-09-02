-- Background feeds that push events into the bar. They are restarted on
-- every (re)load so a config reload never leaves a duplicate behind.
local h = require("helpers")

local START = [[
killall stats_provider >/dev/null 2>&1
pkill -f '[m]acmon pipe --interval 3000' >/dev/null 2>&1
if command -v stats_provider >/dev/null 2>&1; then
  iface="$(route -n get default 2>/dev/null | awk '/interface:/{print $2; exit}')"
  if [ -n "$iface" ]; then
    nohup stats_provider --cpu usage --memory ram_usage --network "$iface" --interval 3 --network-refresh-rate 10 >/dev/null 2>&1 &
  else
    nohup stats_provider --cpu usage --memory ram_usage --interval 3 >/dev/null 2>&1 &
  fi
fi
if command -v macmon >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
  nohup ]] .. h.q(PLUGIN_DIR .. "/gpu_provider.sh") .. [[ >/dev/null 2>&1 &
fi
exit 0
]]

sbar.exec("PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin; " .. START)

-- Sync the workspace and focus state with aerospace once everything exists.
h.exec("aerospace list-workspaces --focused 2>/dev/null", function(workspace)
  if workspace ~= "" then
    sbar.trigger("aerospace_workspace_change", { FOCUSED_WORKSPACE = workspace })
  end
end)
h.exec("aerospace list-windows --focused --format '%{window-id}' 2>/dev/null", function(window_id)
  sbar.trigger("aerospace_focus_change", { WINDOW_ID = window_id })
end)
