return {
  "nvim-treesitter/nvim-treesitter",
  branch = "main", -- New rewrite (requires Neovim 0.11+)
  lazy = false,
  build = ":TSUpdate",
  config = function()
    require("nvim-treesitter").setup({
      install_dir = vim.fn.stdpath("data") .. "/site",
    })

    -- Install parsers (async, no-op if already installed)
    require("nvim-treesitter").install({
      "bash",
      "c",
      "comment",
      "css",
      "diff",
      "dockerfile",
      "go",
      "gomod",
      "gosum",
      "hcl",
      "html",
      "javascript",
      "json",
      "jsonc",
      "kdl",
      "lua",
      "luadoc",
      "markdown",
      "markdown_inline",
      "nix",
      "python",
      "query",
      "rust",
      "scss",
      "terraform",
      "toml",
      "tsx",
      "typescript",
      "vim",
      "vimdoc",
      "yaml",
    })
  end,
}
