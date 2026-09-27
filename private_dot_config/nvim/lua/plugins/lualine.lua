local palette = require("themes.nocturne-rose.palette")
local function mode(color)
  return {
    a = { fg = palette.base, bg = color, gui = "bold" },
    b = { fg = palette.text, bg = palette.overlay },
    c = { fg = palette.subtext, bg = palette.mantle },
  }
end

require("lualine").setup({
  options = {
    theme = {
      normal = mode(palette.rose),
      insert = mode(palette.green),
      visual = mode(palette.orchid),
      replace = mode(palette.red),
      command = mode(palette.yellow),
      inactive = mode(palette.muted),
    },
    globalstatus = true,
    icons_enabled = false,
    component_separators = "|",
    section_separators = "",
  },
  sections = {
    lualine_a = { "mode" },
    lualine_b = { "branch", "diff", "diagnostics" },
    lualine_c = { { "filename", path = 1 } },
    lualine_x = { "encoding", "filetype" },
    lualine_y = { "progress" },
    lualine_z = { "location" },
  },
  extensions = { "oil", "quickfix" },
})
