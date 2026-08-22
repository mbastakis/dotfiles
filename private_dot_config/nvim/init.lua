vim.g.mapleader = " "
vim.g.maplocalleader = " "

require("config.options")
require("config.autocmds")
require("config.plugins")
require("config.treesitter")
require("config.completion")
require("config.lsp")
require("config.format")
require("config.lint")
require("config.supermaven")
require("config.themes").setup()
require("plugins.gitsigns")
require("plugins.oil")
require("plugins.pick")
require("plugins.surround")
require("config.keymaps")
