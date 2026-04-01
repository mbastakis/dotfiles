# LSP Custom Configs

Files here **override** nvim-lspconfig defaults.

## Quick Start

Create `after/lsp/SERVER_NAME.lua`:

```lua
-- Example: after/lsp/ts_ls.lua
return {
  settings = {
    typescript = {
      inlayHints = {
        includeInlayParameterNameHints = "all",
      },
    },
  },
}
```

Restart Neovim. Done! ✅

## Common Overrides

### Disable diagnostics
```lua
return {
  on_attach = function(client)
    client.server_capabilities.documentFormattingProvider = false
  end
}
```

### Add custom filetypes
```lua
return {
  filetypes = { "html", "css", "javascript", "typescript", "vue" },
}
```

### Custom root detection
```lua
return {
  root_dir = vim.fs.root(0, { "Cargo.toml", ".git" }),
}
```

### Server-specific settings
```lua
return {
  settings = {
    Lua = {
      diagnostics = { globals = { "vim" } },
      workspace = { checkThirdParty = false },
    }
  }
}
```

If you need to enable a non-Mason server manually, call `vim.lsp.enable("server_name")`
from your normal config after defining its `after/lsp/server_name.lua` table.

## See Also

- `:help lsp-config` - Full documentation
- `:LspInfo` - View active servers
- Check `lua_ls.lua` in this dir for a working example
