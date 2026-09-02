-- Battery: quiet at rest; pill + colored border appear only for low,
-- critical and charging states.
local colors = require("colors")
local settings = require("settings")
local h = require("helpers")

local ICONS = { "󰂎", "󰁺", "󰁻", "󰁼", "󰁽", "󰁾", "󰁿", "󰂀", "󰂁", "󰂂", "󰁹" }

local item = sbar.add("item", "battery", {
  position = "right",
  icon = { string = "󰁹", color = colors.SUBTEXT_COLOR },
  label = { string = "--%", font = settings.bold(13) },
  padding_left = 0,
  padding_right = 0,
  update_freq = 120,
  background = {
    drawing = false,
    border_width = 0,
    border_color = colors.BORDER_COLOR,
  },
})

item:subscribe("mouse.clicked", function()
  sbar.exec("open 'x-apple.systempreferences:com.apple.preference.battery'")
end)

local function update()
  h.exec("pmset -g batt 2>/dev/null", function(status)
    local percentage = tonumber(status:match("(%d+)%%"))
    if not percentage then
      item:set({ drawing = false })
      return
    end
    local icon = ICONS[math.min(#ICONS, math.floor(percentage / 10) + 1)]
    local color, pill, border_width, border_color = colors.SUBTEXT_COLOR, false, 0, colors.BORDER_COLOR
    if percentage <= 10 then
      color, pill, border_width, border_color = colors.ERROR_COLOR, true, 1, colors.ERROR_COLOR
    elseif percentage <= 25 then
      color, pill, border_width, border_color = colors.WARNING_COLOR, true, 1, colors.WARNING_COLOR
    end
    if status:find("AC Power") or status:find("charging") or status:find("charged") then
      icon = "󰂄"
      color, pill, border_width, border_color = colors.INFO_COLOR, true, 1, colors.INFO_COLOR
    end
    sbar.animate("tanh", 12, function()
      item:set({
        drawing = true,
        icon = { string = icon, color = color },
        label = { string = percentage .. "%", color = colors.TEXT_COLOR },
        background = { drawing = pill, border_width = border_width, border_color = border_color },
      })
    end)
  end)
end

item:subscribe({ "power_source_change", "system_woke", "routine", "forced" }, update)
