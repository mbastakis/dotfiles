# Neovim Configuration

lazy.nvim plugin manager with LSP, formatting, and linting. Theme: Catppuccin Mocha.

## Structure

| Path               | Purpose                                    |
| ------------------ | ------------------------------------------ |
| `init.lua`         | Entry point, bootstraps lazy.nvim          |
| `lua/config/`      | Core settings (options, keymaps, autocmds) |
| `lua/plugins/`     | Plugin specs (one file per plugin)         |
| `lua/plugins/lsp/` | LSP-related plugins                        |
| `after/lsp/*.lua`  | Server-specific overrides                  |
| `test/`            | Test files for LSP validation              |

## Commands

| Command                           | Purpose            |
| --------------------------------- | ------------------ |
| `nvim --headless +q`              | Validate syntax    |
| `nvim -c ':checkhealth' -c ':qa'` | Full health check  |
| `:Lazy`                           | Plugin manager UI  |
| `:Mason`                          | LSP/tool installer |
| `:LspInfo`                        | Active LSP servers |
| `:ConformInfo`                    | Formatter status   |

## LSP Architecture

| File              | Purpose                             |
| ----------------- | ----------------------------------- |
| `lsp/mason.lua`   | Install servers via Mason           |
| `lsp/config.lua`  | LSP keymaps, diagnostics            |
| `linting.lua`     | nvim-lint rules by filetype         |
| `formatting.lua`  | conform.nvim (format on save)       |
| `after/lsp/*.lua` | Server overrides (highest priority) |

## Adding Plugins

Create `lua/plugins/<name>.lua`:

```lua
return {
  "author/plugin-name",
  dependencies = { "dep/plugin" },
  opts = {
    option = "value",
  },
}
```

## Adding LSP Servers

1. Add to `ensure_installed` in `lua/plugins/lsp/mason.lua`
2. (Optional) Create `after/lsp/<server>.lua` for overrides:

```lua
vim.lsp.config("server_name", {
  settings = {
    -- server-specific settings
  },
})
```

## Code Style

- **Indentation**: 2 spaces
- **Strings**: double quotes preferred
- **Tables**: trailing commas
- **Formatter**: stylua (`.stylua.toml`)
- **Linter**: selene (`selene.toml`)

```lua
-- Keymap convention
vim.keymap.set("n", "<leader>key", func, { desc = "Description" })
```

## Gotchas

- **Do not** edit `lazy-lock.json` manually — managed by lazy.nvim
- Server overrides in `after/lsp/` take precedence over plugin config
- Test files in `test/` are for LSP validation, not symlinked to home
- See `after/lsp/README.md` for server override documentation
