return {
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    main = "nvim-treesitter.configs",
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
        "jsonc",
        "jsdoc",
        "graphql",

        -- Programming Languages
        "python",
        "go",
        "gomod",
        "gowork",
        "rust",
        "c",

        -- DevOps/IaC
        "yaml",
        "helm",
        "terraform",
        "hcl",
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
        "proto",
        "requirements",

        -- Utilities
        "bash",
        "diff",
        "regex",
        "jq",
        "ssh_config",
      },
      auto_install = false,
      highlight = {
        enable = true,
      },
      indent = { enable = true },
    },
  },
}
