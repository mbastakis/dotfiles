-- Aerospace workspaces. Chip anatomy: icon = workspace letter, label = glyphs
-- of the apps living there. Focus comes from aerospace's own hooks
-- (exec-on-workspace-change / on-focus-changed → sketchybar --trigger);
-- window churn comes from sketchybar's native space_windows_change event.
local colors = require("colors")
local settings = require("settings")
local h = require("helpers")
local icon_map = require("icon_map")

local IDS = { "a", "o", "e", "u" }

local spaces = {}
local focused = nil

local function paint(id, animate)
  local space = spaces[id]
  local props
  if id == focused then
    -- Active workspace gets two cues: rose letter plus a subtle rose chip, so
    -- the state survives color-only ambiguity. Glyphs step up to full text.
    props = {
      icon = { color = colors.ACCENT_COLOR },
      label = { color = colors.TEXT_COLOR },
      background = { color = colors.ACCENT_CHIP },
    }
  else
    props = {
      icon = { color = colors.SUBTEXT_COLOR },
      label = { color = colors.MUTED_COLOR },
      background = { color = colors.ACCENT_CHIP_OFF },
    }
  end
  if animate then
    sbar.animate("tanh", 16, function()
      space:set(props)
    end)
  else
    space:set(props)
  end
end

for _, id in ipairs(IDS) do
  local space = sbar.add("item", "space." .. id, {
    position = "left",
    icon = {
      string = id,
      font = settings.bold(14),
      color = colors.SUBTEXT_COLOR,
      padding_left = 10,
      padding_right = 10,
    },
    label = {
      drawing = false,
      font = settings.app(14),
      color = colors.MUTED_COLOR,
      padding_left = 0,
      padding_right = 10,
    },
    background = {
      drawing = true,
      color = colors.ACCENT_CHIP_OFF,
      corner_radius = 6,
      height = 22,
    },
  })
  spaces[id] = space

  space:subscribe("mouse.clicked", function()
    sbar.exec("aerospace workspace " .. id)
  end)

  -- Hover: unfocused letters brighten with a faint chip under the pointer;
  -- the focused workspace already wears its full chip and stays put.
  space:subscribe("mouse.entered", function()
    if id ~= focused then
      sbar.animate("tanh", 8, function()
        space:set({ icon = { color = colors.TEXT_COLOR }, background = { color = colors.ACCENT_CHIP_HOVER } })
      end)
    end
  end)
  space:subscribe("mouse.exited", function()
    if id ~= focused then
      sbar.animate("tanh", 8, function()
        space:set({ icon = { color = colors.SUBTEXT_COLOR }, background = { color = colors.ACCENT_CHIP_OFF } })
      end)
    end
  end)
end

local names = {}
for _, id in ipairs(IDS) do
  names[#names + 1] = "space." .. id
end
sbar.add("bracket", "workspaces", names, settings.bracket)

-- Repaint every workspace's app glyphs in one pass.
local function update_apps()
  h.exec_json("aerospace list-windows --all --format '%{workspace}%{app-name}' --json 2>/dev/null", function(windows)
    if not windows then
      return
    end
    local apps = {}
    for _, id in ipairs(IDS) do
      apps[id] = {}
    end
    for _, window in ipairs(windows) do
      local ws, app = window.workspace, window["app-name"]
      if apps[ws] and app and app ~= "" then
        apps[ws][app] = true
      end
    end
    for _, id in ipairs(IDS) do
      local sorted = {}
      for app in pairs(apps[id]) do
        sorted[#sorted + 1] = app
      end
      table.sort(sorted)
      local glyphs = {}
      for _, app in ipairs(sorted) do
        glyphs[#glyphs + 1] = icon_map[app] or ":default:"
      end
      if #glyphs > 0 then
        spaces[id]:set({
          label = { string = table.concat(glyphs, " "), drawing = true },
          icon = { padding_right = 4 },
        })
      else
        spaces[id]:set({
          label = { string = "", drawing = false },
          icon = { padding_right = 10 },
        })
      end
    end
  end)
end

local function set_focus(id)
  if not id or id == "" then
    return
  end
  focused = id
  for _, ws in ipairs(IDS) do
    if spaces[ws] then
      paint(ws, true)
    end
  end
end

-- Invisible root that owns the subscriptions for the whole group.
local root = sbar.add("item", "aerospace_root", {
  position = "left",
  drawing = false,
  updates = true,
  update_freq = 60,
})

root:subscribe("aerospace_workspace_change", function(env)
  set_focus(env.FOCUSED_WORKSPACE)
  update_apps()
end)

root:subscribe({
  "aerospace_focus_change",
  "front_app_switched",
  "space_windows_change",
  "display_change",
  "system_woke",
  "routine",
  "forced",
}, function()
  update_apps()
end)

h.exec("aerospace list-workspaces --focused 2>/dev/null", function(result)
  set_focus(result)
  update_apps()
end)
