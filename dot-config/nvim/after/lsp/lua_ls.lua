-- Custom configuration for lua_ls (Lua Language Server)
-- This file is automatically loaded by Neovim's LSP system

vim.lsp.config('lua_ls', {
  settings = {
    Lua = {
      -- Recognize 'vim' global in Neovim config files
      diagnostics = {
        globals = { "vim" }
      },
      -- Disable third-party library checks (speeds up startup)
      workspace = {
        checkThirdParty = false,
      },
      -- Disable telemetry
      telemetry = {
        enable = false,
      },
    }
  }
})
