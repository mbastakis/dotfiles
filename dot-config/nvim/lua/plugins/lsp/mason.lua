-- Mason: Package manager for LSP servers, DAP servers, linters, and formatters
-- mason-lspconfig: Bridge between mason.nvim and nvim-lspconfig
-- mason-tool-installer: Automatically install tools via Mason

return {
  -- nvim-lspconfig: Quickstart configs for Neovim LSP
  -- Must be in runtimepath before mason-lspconfig
  {
    "neovim/nvim-lspconfig",
  },

  -- Mason core
  {
    "mason-org/mason.nvim",
    opts = {
      ui = {
        icons = {
          package_installed = "✓",
          package_pending = "➜",
          package_uninstalled = "✗"
        }
      }
    }
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
        "lua_ls",      -- Lua
        "ts_ls",       -- TypeScript/JavaScript
        "eslint",      -- ESLint
      },
      -- Automatically enable installed servers (default: true)
      -- Custom per-server configs in lua/plugins/lsp/servers/
      automatic_enable = true,
    }
  },

  -- Mason tool installer (for formatters, linters, etc.)
  {
    "WhoIsSethDaniel/mason-tool-installer.nvim",
    dependencies = { "mason.nvim" },
    opts = {
      ensure_installed = {
        "prettier",    -- Formatter
        "eslint_d",    -- Linter
        "stylua",      -- Lua formatter
      }
    }
  },
}
