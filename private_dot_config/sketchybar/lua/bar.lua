local colors = require("colors")
local settings = require("settings")

sbar.bar({
  height = 40,
  position = "top",
  sticky = true,
  topmost = "window",
  shadow = true,
  color = colors.BAR_COLOR,
  border_width = 0,
  corner_radius = 12,
  padding_left = 8,
  padding_right = 8,
  margin = 8,
  y_offset = 6,
  notch_width = 188,
  display = "all",
})

sbar.default({
  updates = "when_shown",
  icon = {
    font = settings.bold(16),
    color = colors.SUBTEXT_COLOR,
    padding_left = 8,
    padding_right = 4,
  },
  label = {
    font = settings.regular(13),
    color = colors.TEXT_COLOR,
    padding_left = 4,
    padding_right = 8,
  },
  background = {
    color = colors.ITEM_COLOR,
    height = 30,
    corner_radius = 8,
    drawing = false,
  },
  padding_left = 4,
  padding_right = 4,
})
