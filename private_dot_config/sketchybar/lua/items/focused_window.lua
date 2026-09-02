-- Center: app icon + "App · Window title" of the focused window.
local h = require("helpers")

local item = sbar.add("item", "focused_window", {
  position = "center",
  width = "dynamic",
  icon = {
    string = "",
    width = 24,
    padding_left = 0,
    padding_right = 8,
    background = { image = { scale = 0.7 } },
  },
  label = {
    string = "",
    align = "center",
    max_chars = 0,
  },
  background = { drawing = false },
  update_freq = 5,
})

local function update()
  h.exec_json("aerospace list-windows --focused --format '%{app-name}%{window-title}' --json 2>/dev/null", function(windows)
    local window = windows and windows[1]
    local app = window and window["app-name"] or ""
    if app == "" then
      item:set({ drawing = false })
      return
    end
    local title = h.strip_emoji(tostring(window["window-title"] or ""))
    local label = app
    if title ~= "" and title ~= app then
      label = app .. " · " .. title
    end
    item:set({
      drawing = true,
      icon = { background = { image = "app." .. app } },
      label = { string = label },
    })
  end)
end

item:subscribe({ "aerospace_focus_change", "front_app_switched", "system_woke", "routine", "forced" }, update)
