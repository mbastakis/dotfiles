return {
  "nvim-lualine/lualine.nvim",
  config = function()
    local colors = require("catppuccin.palettes").get_palette("mocha")

    local bubbles_theme = {
      normal = {
        a = { fg = colors.base, bg = colors.lavender, gui = "bold" },
        b = { fg = colors.text, bg = colors.surface0 },
        c = { fg = colors.text, bg = colors.mantle },
      },

      insert = { a = { fg = colors.base, bg = colors.blue, gui = "bold" } },
      visual = { a = { fg = colors.base, bg = colors.mauve, gui = "bold" } },
      replace = { a = { fg = colors.base, bg = colors.red, gui = "bold" } },
      command = { a = { fg = colors.base, bg = colors.peach, gui = "bold" } },

      inactive = {
        a = { fg = colors.overlay1, bg = colors.surface0 },
        b = { fg = colors.overlay1, bg = colors.surface0 },
        c = { fg = colors.overlay1, bg = colors.mantle },
      },
    }

    require("lualine").setup({
      options = {
        icons_enabled = true,
        theme = bubbles_theme,
        component_separators = "",
        section_separators = { left = "", right = "" },
        disabled_filetypes = {
          statusline = {},
          winbar = {},
        },
        ignore_focus = {},
        always_divide_middle = true,
        always_show_tabline = false,
        globalstatus = false,
        refresh = {
          statusline = 1000,
          tabline = 1000,
          winbar = 1000,
          refresh_time = 16, -- ~60fps
          events = {
            "WinEnter",
            "BufEnter",
            "BufWritePost",
            "SessionLoadPost",
            "FileChangedShellPost",
            "VimResized",
            "Filetype",
            "CursorMoved",
            "CursorMovedI",
            "ModeChanged",
          },
        },
      },
      sections = {
        lualine_a = {
          { "mode", separator = { left = "" }, right_padding = 2 },
        },
        lualine_b = { "branch", "diff", "diagnostics" },
        lualine_c = { "filename" },
        lualine_x = { "encoding", "filetype" },
        lualine_y = { "progress" },
        lualine_z = {
          { "location", separator = { right = "" }, left_padding = 2 },
        },
      },
      inactive_sections = {
        lualine_a = {
          { "filename", separator = { left = "" }, right_padding = 2 },
        },
        lualine_b = {},
        lualine_c = {},
        lualine_x = {},
        lualine_y = {},
        lualine_z = {
          { "location", separator = { right = "" }, left_padding = 2 },
        },
      },
      tabline = {},
      winbar = {},
      inactive_winbar = {},
      extensions = {},
    })
  end,
}
