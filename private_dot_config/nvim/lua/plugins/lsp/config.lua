-- LSP Configuration and Keymaps
-- nvim-lspconfig: Quickstart configs for Neovim LSP

return {
  "neovim/nvim-lspconfig",
  config = function()
    -- Setup LSP keymaps when LSP attaches to a buffer
    vim.api.nvim_create_autocmd("LspAttach", {
      group = vim.api.nvim_create_augroup("lsp-attach-keymaps", { clear = true }),
      callback = function(event)
        local map = function(keys, func, desc)
          vim.keymap.set("n", keys, func, { buffer = event.buf, desc = "LSP: " .. desc })
        end

        -- Navigation
        map("gd", vim.lsp.buf.definition, "Go to definition")
        map("gD", vim.lsp.buf.declaration, "Go to declaration")
        map("gr", vim.lsp.buf.references, "Go to references")
        map("gI", vim.lsp.buf.implementation, "Go to implementation")
        map("gy", vim.lsp.buf.type_definition, "Go to type definition")

        -- Documentation
        map("K", function()
          vim.lsp.buf.hover({ border = "rounded", max_height = 25, max_width = 120 })
        end, "Hover documentation")

        -- Code actions
        map("<leader>ca", vim.lsp.buf.code_action, "Code action")
        map("<leader>rn", vim.lsp.buf.rename, "Rename symbol")

        -- Diagnostics
        map("<leader>d", vim.diagnostic.open_float, "Show line diagnostics")
        map("<leader>q", vim.diagnostic.setloclist, "Open diagnostics list")
      end,
    })

    -- Configure diagnostic display
    vim.diagnostic.config({
      virtual_text = false,
      signs = {
        text = {
          [vim.diagnostic.severity.ERROR] = "✘",
          [vim.diagnostic.severity.WARN] = "⚠",
          [vim.diagnostic.severity.HINT] = "󰌶",
          [vim.diagnostic.severity.INFO] = "",
        },
      },
      underline = true,
      update_in_insert = false,
      severity_sort = true,
      float = {
        border = "rounded",
        source = true,
        header = "",
        prefix = "",
      },
    })
  end,
}
