-- Mason: Package manager for LSP servers, DAP servers, linters, and formatters
-- mason-lspconfig: Bridge between mason.nvim and nvim-lspconfig
-- mason-tool-installer: Automatically install tools via Mason

return {
  -- Mason core
  {
    "mason-org/mason.nvim",
    opts = {
      ui = {
        icons = {
          package_installed = "✓",
          package_pending = "➜",
          package_uninstalled = "✗",
        },
      },
    },
  },

  -- Mason-lspconfig bridge
  {
    "mason-org/mason-lspconfig.nvim",
    dependencies = {
      "mason.nvim",
      "nvim-lspconfig",
    },
    opts = {
      -- Servers to auto-install if not present
      ensure_installed = {
        "lua_ls", -- Lua
        "ts_ls", -- TypeScript/JavaScript
        "eslint", -- ESLint
      },
      automatic_enable = true,
    },
  },

  -- Mason tool installer (for formatters, linters, etc.)
  {
    "WhoIsSethDaniel/mason-tool-installer.nvim",
    dependencies = { "mason.nvim" },
    opts = {
      ensure_installed = {
        -- Formatters
        "prettier", -- JS/TS/JSON/YAML/Markdown formatter
        "prettierd", -- Faster prettier daemon
        "stylua", -- Lua formatter
        "black", -- Python formatter
        "isort", -- Python import sorter
        "shfmt", -- Shell script formatter

        -- Linters
        "eslint_d", -- JS/TS linter (fast daemon)
        "selene", -- Lua linter (modern, doesn't require luarocks)
        "shellcheck", -- Shell script linter
        "markdownlint", -- Markdown linter
        "pylint", -- Python linter
        "ruff", -- Fast Python linter
        "yamllint", -- YAML linter
        "jsonlint", -- JSON linter
        "hadolint", -- Dockerfile linter
      },
    },
  },
}
