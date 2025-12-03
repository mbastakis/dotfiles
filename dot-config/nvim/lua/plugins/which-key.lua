return {
  "folke/which-key.nvim",
  event = "VeryLazy",
  opts = {
    preset = "helix",
    delay = 500,
    icons = {
      breadcrumb = "»",
      separator = "➜",
      group = " ",
    },
    win = {
      border = "rounded",
      padding = { 1, 2 },
    },
    layout = {
      spacing = 3,
    },
  },
  config = function(_, opts)
    local wk = require("which-key")
    wk.setup(opts)

    -- Register leader key groups
    wk.add({
      { "<leader>f", group = "Find", icon = " " },
      { "<leader>e", group = "Explorer", icon = " " },
      { "<leader>o", group = "Opencode", icon = "󱚟 " },
      { "<leader>g", group = "Git" },
      { "<leader>u", group = "Utilities", icon = " " },
    })
  end,
}
