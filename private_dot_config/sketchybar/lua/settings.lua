local colors = require("colors")

-- Type scale: icons Bold:16, labels Regular:13, informational labels Bold:13,
-- workspace letters Bold:14. Spacing grid: 4 / 8 / 12.
local M = {}

M.font = "JetBrainsMono Nerd Font Mono"
M.app_font = "sketchybar-app-font"

function M.bold(size)
  return string.format("%s:Bold:%.1f", M.font, size)
end

function M.regular(size)
  return string.format("%s:Regular:%.1f", M.font, size)
end

function M.app(size)
  return string.format("%s:Regular:%.1f", M.app_font, size)
end

-- Gap between pills on the right side.
M.pill_gap = 4

-- Shared popup chrome: same surface as the bar, hairline border, soft blur.
M.popup = {
  y_offset = 6,
  blur_radius = 20,
  background = {
    color = colors.BAR_COLOR,
    corner_radius = 10,
    border_width = 1,
    border_color = colors.BORDER_COLOR,
  },
}

-- Bracket chrome shared by every pill on the bar.
M.bracket = {
  background = {
    drawing = true,
    color = colors.ITEM_COLOR,
    height = 30,
    corner_radius = 8,
    border_width = 1,
    border_color = colors.BORDER_COLOR,
  },
}

-- Icon-only toggle: 36pt wide, glyph centered, no item padding.
function M.icon_button(glyph)
  return {
    width = 36,
    padding_left = 0,
    padding_right = 0,
    icon = {
      string = glyph,
      color = colors.MUTED_COLOR,
      align = "center",
      width = 36,
      padding_left = 0,
      padding_right = 0,
    },
    label = { drawing = false },
    background = { drawing = false },
  }
end

-- Clickable popup row: glyph column + text, hover chip drawn by helpers.
M.popup_row = {
  padding_left = 6,
  padding_right = 6,
  icon = {
    font = M.bold(15),
    width = 30,
    align = "center",
    padding_left = 0,
    padding_right = 2,
  },
  label = {
    font = M.regular(13),
    padding_left = 2,
    padding_right = 10,
  },
  background = {
    drawing = true,
    color = colors.ACCENT_CHIP_OFF,
    height = 26,
    corner_radius = 6,
  },
}

-- Small section header inside a vertical popup (rows all share one height,
-- so headers replace hairline separators).
M.popup_header = {
  padding_left = 8,
  padding_right = 8,
  icon = { drawing = false },
  label = {
    font = M.bold(11),
    color = colors.SUBTEXT_COLOR,
    padding_left = 4,
    padding_right = 8,
  },
  background = { drawing = false },
}

return M
