return {
  "stevearc/conform.nvim",
  opts = {},
  config = function()
    require("conform").setup({
      formatters_by_ft = {
        -- Lua
        lua = { "stylua" },

        -- Python (run isort first for imports, then black for code)
        python = { "isort", "black" },

        -- JavaScript/TypeScript (prettierd is faster)
        javascript = { "prettierd", "prettier", stop_after_first = true },
        typescript = { "prettierd", "prettier", stop_after_first = true },
        javascriptreact = { "prettierd", "prettier", stop_after_first = true },
        typescriptreact = { "prettierd", "prettier", stop_after_first = true },

        -- JSON/YAML/Markdown (prettier handles these well)
        json = { "prettierd", "prettier", stop_after_first = true },
        yaml = { "prettierd", "prettier", stop_after_first = true },
        markdown = { "prettierd", "prettier", stop_after_first = true },

        -- Shell scripts
        sh = { "shfmt" },
        bash = { "shfmt" },
        zsh = { "shfmt" },

        -- Rust (use rustfmt via LSP as fallback)
        rust = { "rustfmt", lsp_format = "fallback" },
      },
      format_on_save = {
        -- These options will be passed to conform.format()
        timeout_ms = 500,
        lsp_format = "fallback",
      },
    })
    vim.api.nvim_create_autocmd("BufWritePre", {
      pattern = "*",
      callback = function(args)
        require("conform").format({ bufnr = args.buf })
      end,
    })
  end,
}
