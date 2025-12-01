# LSP Custom Configs

Files here **override** nvim-lspconfig defaults.

## Quick Start

Create `after/lsp/SERVER_NAME.lua`:

```lua
-- Example: after/lsp/ts_ls.lua
vim.lsp.config('ts_ls', {
  settings = {
    typescript = {
      inlayHints = {
        includeInlayParameterNameHints = 'all',
      }
    }
  }
})
```

Restart Neovim. Done! ✅

## Common Overrides

### Disable diagnostics
```lua
vim.lsp.config('eslint', {
  on_attach = function(client)
    client.server_capabilities.documentFormattingProvider = false
  end
})
```

### Add custom filetypes
```lua
vim.lsp.config('tailwindcss', {
  filetypes = { 'html', 'css', 'javascript', 'typescript', 'vue' }
})
```

### Custom root detection
```lua
vim.lsp.config('rust_analyzer', {
  root_dir = vim.fs.root(0, {'Cargo.toml', '.git'})
})
```

### Server-specific settings
```lua
vim.lsp.config('lua_ls', {
  settings = {
    Lua = {
      diagnostics = { globals = { 'vim' } },
      workspace = { checkThirdParty = false },
    }
  }
})
```

## See Also

- `:help lsp-config` - Full documentation
- `:LspInfo` - View active servers
- Check `lua_ls.lua` in this dir for a working example
