vim.g.mapleader = " "
vim.g.maplocalleader = " "

require("config.options")
require("config.autocmds")
require("config.plugins")
require("config.treesitter")
require("config.completion")
require("config.themes").setup()
require("tiny-inline-diagnostic").setup({
  options = { show_source = { enabled = true } },
})
require("config.lsp")
require("config.format")
require("config.lint")
require("config.supermaven")
require("plugins.gitsigns")
require("plugins.oil")
require("plugins.telescope")
require("plugins.hlslens")
require("plugins.lualine")
require("plugins.surround")
require("config.keymaps")

local which_key = require("which-key")
which_key.setup({
  delay = 300,
  preset = "classic",
})
which_key.add({
  { "<leader>c", group = "Code" },
  { "<leader>f", group = "Find / format" },
  { "<leader>g", group = "Git" },
  { "<leader>i", group = "Images" },
  { "<leader>r", group = "Rename" },
  { "<leader>u", group = "UI / toggles" },
})
vim.keymap.set("n", "<leader>?", function()
  which_key.show({ global = false })
end, { desc = "Show buffer keymaps" })
