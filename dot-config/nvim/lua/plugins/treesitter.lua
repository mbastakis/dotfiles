return {
  "nvim-treesitter/nvim-treesitter",
  build = ":TSUpdate",
  main = "nvim-treesitter.configs", -- Sets main module to use for opts
  -- [[ Configure Treesitter ]] See `:help nvim-treesitter`
  opts = {
    ensure_installed = {
      -- Core/Vim
      "vim",
      "vimdoc",
      "lua",
      "luadoc",
      "query",
      "comment",

      -- Web Development
      "html",
      "css",
      "javascript",
      "typescript",
      "tsx",
      "json",
      "jsonc", -- JSON with Comments
      "jsdoc", -- JSDoc comments
      "graphql", -- GraphQL

      -- Programming Languages
      "python",
      "go",
      "gomod",
      "gowork",
      "rust",
      "c",

      -- DevOps/IaC
      "yaml",
      "helm", -- Helm templates
      "terraform",
      "hcl", -- HashiCorp Config
      "dockerfile",
      "make",
      "nix",
      "toml",
      "sql",

      -- Git
      "git_config",
      "git_rebase",
      "gitcommit",
      "gitignore",
      "gitattributes",

      -- Documentation
      "markdown",
      "markdown_inline",

      -- Config/Data Formats
      "xml",
      "proto", -- Protocol Buffers
      "requirements", -- Python requirements.txt

      -- Utilities
      "bash",
      "diff",
      "regex",
      "jq", -- JSON query
      "ssh_config",
    },
    -- Autoinstall languages that are not installed
    auto_install = false,
    highlight = {
      enable = true,
      -- Some languages depend on vim's regex highlighting system (such as Ruby) for indent rules.
      --  If you are experiencing weird indenting issues, add the language to
      --  the list of additional_vim_regex_highlighting and disabled languages for indent.
      additional_vim_regex_highlighting = { "ruby" },
    },
    indent = { enable = true, disable = { "ruby" } },
  },
  -- There are additional nvim-treesitter modules that you can use to interact
  -- with nvim-treesitter. You should go explore a few and see what interests you:
  --
  --    - Incremental selection: Included, see `:help nvim-treesitter-incremental-selection-mod`
  --    - Show your current context: https://github.com/nvim-treesitter/nvim-treesitter-context
  --    - Treesitter + textobjects: https://github.com/nvim-treesitter/nvim-treesitter-textobjects
}
