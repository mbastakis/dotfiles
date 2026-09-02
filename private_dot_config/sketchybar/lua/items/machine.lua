-- Machine pill: display mode, input source, Amphetamine, system stats.
local colors = require("colors")
local settings = require("settings")
local h = require("helpers")

h.spacer("gap.machine", settings.pill_gap)

-- --- display mode ---------------------------------------------------------------
-- The native mode is the quiet default: icon only. A label appears only when
-- the display is in a non-default mode.
local DISPLAY_NAME = "LC49G95T"
local NATIVE_MODE = "204"
local SCALED_MODE = "79"

local display_mode = sbar.add("item", "display_mode", {
  position = "right",
  icon = { string = "󰍹", color = colors.MUTED_COLOR, padding_left = 6, padding_right = 8 },
  label = {
    drawing = false,
    font = settings.bold(13),
    color = colors.SUBTEXT_COLOR,
    padding_left = 0,
    padding_right = 8,
  },
  padding_left = 0,
  padding_right = 0,
  update_freq = 10,
})

local function query_display(callback)
  h.exec("command -v betterdisplaycli >/dev/null 2>&1 && betterdisplaycli get -namelike=" .. DISPLAY_NAME
    .. " -displaymodenumber 2>/dev/null", callback)
end

local function update_display()
  query_display(function(mode)
    if mode == "" then
      display_mode:set({ drawing = false })
    elseif mode == NATIVE_MODE then
      display_mode:set({ drawing = true, label = { drawing = false } })
    elseif mode == SCALED_MODE then
      display_mode:set({ drawing = true, label = { drawing = true, string = "Normal" } })
    else
      h.exec("betterdisplaycli get -namelike=" .. DISPLAY_NAME .. " -resolution 2>/dev/null", function(resolution)
        local label = resolution:match("^(%d+)") or "N/A"
        display_mode:set({ drawing = true, label = { drawing = true, string = label } })
      end)
    end
  end)
end

display_mode:subscribe({ "routine", "forced", "system_woke", "display_change" }, update_display)
display_mode:subscribe("mouse.clicked", function()
  query_display(function(mode)
    local target = mode == NATIVE_MODE and SCALED_MODE or NATIVE_MODE
    h.exec("betterdisplaycli set -namelike=" .. DISPLAY_NAME .. " -displaymodenumber=" .. target .. " >/dev/null 2>&1", function()
      sbar.delay(1, update_display)
    end)
  end)
end)

-- --- input source ------------------------------------------------------------------
-- Event driven: macOS posts a distributed notification on every layout
-- change, so no polling.
local LAYOUT_LABELS = { ABC = "EN", Dvorak = "DV", GreekDvorak = "EL", ["Greek Dvorak"] = "EL" }

local input_source = sbar.add("item", "input_source", {
  position = "right",
  icon = { drawing = false },
  label = {
    string = "--",
    font = settings.bold(13),
    color = colors.SUBTEXT_COLOR,
    padding_left = 6,
    padding_right = 6,
  },
  padding_left = 0,
  padding_right = 0,
})

local function update_input_source()
  h.exec("defaults read com.apple.HIToolbox AppleSelectedInputSources 2>/dev/null", function(plist)
    local layout = plist:match('"?KeyboardLayout Name"?%s*=%s*"?([^";]+)"?;') or ""
    local label = LAYOUT_LABELS[layout] or layout:sub(1, 2)
    if label == "" then
      label = "--"
    end
    input_source:set({ label = { string = label } })
  end)
end

input_source:subscribe({ "input_source_change", "system_woke", "forced" }, update_input_source)
input_source:subscribe("mouse.clicked", function()
  h.exec(os.getenv("HOME") .. "/bin/switch-input-source >/dev/null 2>&1", function()
    sbar.delay(0.3, update_input_source)
  end)
end)
update_input_source()

-- --- amphetamine ------------------------------------------------------------------
-- Dim icon at rest; label + amber border only while a session is active.
local amphetamine = sbar.add("item", "amphetamine", {
  position = "right",
  icon = { string = "󰒲", color = colors.MUTED_COLOR, padding_left = 6, padding_right = 6 },
  label = { drawing = false, font = settings.bold(13), padding_left = 0, padding_right = 8 },
  padding_left = 0,
  padding_right = 0,
  background = { drawing = false, border_width = 0 },
  update_freq = 30,
})

local AMPHETAMINE_QUERY = "/usr/bin/osascript -e 'tell application \"Amphetamine\" to return "
  .. "(session is active as text) & \"|\" & (session time remaining as text)' 2>/dev/null"

local function update_amphetamine()
  h.exec(AMPHETAMINE_QUERY, function(result)
    local active, remaining = result:match("^(%a+)|(%-?%d+)")
    if active ~= "true" then
      sbar.animate("tanh", 12, function()
        amphetamine:set({
          icon = { color = colors.MUTED_COLOR },
          label = { drawing = false },
          background = { drawing = false, border_width = 0 },
        })
      end)
      return
    end
    remaining = tonumber(remaining) or 0
    local label
    if remaining == 0 then
      label = "∞"
    elseif remaining == -1 then
      label = "trigger"
    elseif remaining == -2 then
      label = "active"
    elseif remaining >= 3600 then
      label = string.format("%dh %dm", remaining // 3600, (remaining % 3600) // 60)
    else
      label = string.format("%dm", remaining // 60)
    end
    sbar.animate("tanh", 12, function()
      amphetamine:set({
        icon = { color = colors.WARNING_COLOR },
        label = { drawing = true, string = label, color = colors.TEXT_COLOR },
        background = { drawing = true, border_width = 1, border_color = colors.WARNING_COLOR },
      })
    end)
  end)
end

amphetamine:subscribe({ "routine", "forced", "system_woke" }, update_amphetamine)
amphetamine:subscribe("mouse.clicked", function(env)
  if env.BUTTON == "right" then
    sbar.exec("/usr/bin/open -a Amphetamine")
    return
  end
  h.exec(AMPHETAMINE_QUERY, function(result)
    local action = result:match("^true") and "end session" or "start new session"
    h.exec("/usr/bin/osascript -e 'tell application \"Amphetamine\" to " .. action .. "' >/dev/null 2>&1", update_amphetamine)
  end)
end)

-- --- system stats -----------------------------------------------------------------
local stats = sbar.add("item", "stats", h.merge(settings.icon_button("󰍛"), { position = "right" }))

local panel = {}
local panel_defaults = {
  position = "right",
  drawing = false,
  updates = true,
  padding_left = 4,
  padding_right = 4,
  background = { drawing = false },
  label = { color = colors.SUBTEXT_COLOR },
}
panel.network = sbar.add("item", "network", h.merge(panel_defaults, { icon = "󰛳", label = "↓ --  ↑ --" }))
panel.cpu = sbar.add("item", "cpu", h.merge(panel_defaults, { icon = "󰍛", label = "CPU --" }))
panel.gpu = sbar.add("item", "gpu", h.merge(panel_defaults, { icon = "󰢮", label = "GPU --" }))
panel.ram = sbar.add("item", "ram", h.merge(panel_defaults, { icon = "󰘚", label = "RAM --" }))
panel.disk = sbar.add("item", "disk", h.merge(panel_defaults, { icon = "󰋊", label = "DISK --", update_freq = 60 }))
local panel_order = { "network", "cpu", "gpu", "ram", "disk" }

local stats_container = sbar.add("bracket", "stats_container", panel_order, {
  drawing = false,
  background = {
    color = colors.ITEM_COLOR,
    corner_radius = 8,
    height = 30,
    border_width = 1,
    border_color = colors.BORDER_COLOR,
  },
})

local stats_left_gap = sbar.add("item", "stats_left_gap", {
  position = "right",
  drawing = false,
  width = 8,
  padding_left = 0,
  padding_right = 0,
  icon = { drawing = false },
  label = { drawing = false },
  background = { drawing = false },
})

local network_interface = ""
h.exec("route -n get default 2>/dev/null | awk '/interface:/{print $2; exit}'", function(iface)
  network_interface = iface:gsub("[.-]", "_")
end)

panel.cpu:subscribe("system_stats", function(env)
  panel.cpu:set({ label = { string = "CPU " .. (env.CPU_USAGE or "--") } })
end)
panel.ram:subscribe("system_stats", function(env)
  panel.ram:set({ label = { string = "RAM " .. (env.RAM_USAGE or "--") } })
end)
panel.network:subscribe("system_stats", function(env)
  local rx = env["NETWORK_RX_" .. network_interface] or "--"
  local tx = env["NETWORK_TX_" .. network_interface] or "--"
  panel.network:set({ label = { string = "↓ " .. rx .. "  ↑ " .. tx } })
end)
panel.gpu:subscribe("gpu_stats", function(env)
  panel.gpu:set({ label = { string = "GPU " .. (env.GPU_USAGE or "--") } })
end)
panel.disk:subscribe({ "routine", "forced", "system_woke" }, function()
  h.exec("df -H /System/Volumes/Data | awk 'NR == 2 {print $5}'", function(usage)
    panel.disk:set({ label = { string = "DISK " .. (usage ~= "" and usage or "--") } })
  end)
end)

-- The panel fades in place instead of popping: transparent variants of the
-- resting colors are animated to and from.
local CLEAR_SUBTEXT = colors.alpha(colors.SUBTEXT_COLOR, 0)
local CLEAR_ITEM = colors.alpha(colors.ITEM_COLOR, 0)
local CLEAR_BORDER = colors.alpha(colors.BORDER_COLOR, 0)
local panel_open = false

local function toggle_panel()
  if panel_open then
    panel_open = false
    sbar.animate("tanh", 12, function()
      stats:set({ icon = { color = colors.MUTED_COLOR } })
      stats_container:set({ background = { color = CLEAR_ITEM, border_color = CLEAR_BORDER } })
      for _, name in ipairs(panel_order) do
        panel[name]:set({ icon = { color = CLEAR_SUBTEXT }, label = { color = CLEAR_SUBTEXT } })
      end
    end)
    sbar.delay(0.25, function()
      sbar.set("focused_window", { drawing = true })
      stats_left_gap:set({ drawing = false })
      stats_container:set({ drawing = false })
      for _, name in ipairs(panel_order) do
        panel[name]:set({ drawing = false })
      end
    end)
  else
    panel_open = true
    sbar.set("focused_window", { drawing = false })
    stats_left_gap:set({ drawing = true })
    stats_container:set({ drawing = true, background = { color = CLEAR_ITEM, border_color = CLEAR_BORDER } })
    for _, name in ipairs(panel_order) do
      panel[name]:set({ drawing = true, icon = { color = CLEAR_SUBTEXT }, label = { color = CLEAR_SUBTEXT } })
    end
    sbar.animate("tanh", 20, function()
      stats:set({ icon = { color = colors.TEXT_COLOR } })
      stats_container:set({ background = { color = colors.ITEM_COLOR, border_color = colors.BORDER_COLOR } })
      for _, name in ipairs(panel_order) do
        panel[name]:set({ icon = { color = colors.SUBTEXT_COLOR }, label = { color = colors.SUBTEXT_COLOR } })
      end
    end)
  end
end

stats:subscribe("mouse.clicked", toggle_panel)
-- The stats icon stays bright while the panel is open.
h.hover_icon(stats, function()
  return panel_open and colors.TEXT_COLOR or colors.MUTED_COLOR
end)

sbar.add("bracket", "machine", {
  display_mode.name,
  input_source.name,
  amphetamine.name,
  stats.name,
  stats_left_gap.name,
}, settings.bracket)
