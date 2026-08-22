local parsers = {
  "bash",
  "dockerfile",
  "go",
  "gomod",
  "gosum",
  "gotmpl",
  "hcl",
  "javascript",
  "json",
  "lua",
  "markdown",
  "markdown_inline",
  "python",
  "query",
  "terraform",
  "toml",
  "tsx",
  "typescript",
  "vim",
  "vimdoc",
  "yaml",
}

require("nvim-treesitter").setup({
  install_dir = vim.fn.stdpath("data") .. "/site",
})
require("nvim-treesitter").install(parsers)

vim.opt.foldmethod = "expr"
vim.opt.foldexpr = "v:lua.vim.treesitter.foldexpr()"
vim.opt.foldtext = ""
vim.opt.foldlevel = 99
vim.opt.foldlevelstart = 99
vim.opt.foldenable = true
