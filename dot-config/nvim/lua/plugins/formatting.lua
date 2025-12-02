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

        -- HTML/CSS/JavaScript/TypeScript
        html = { "prettierd", "prettier", stop_after_first = true },
        css = { "prettierd", "prettier", stop_after_first = true },
        scss = { "prettierd", "prettier", stop_after_first = true },
        less = { "prettierd", "prettier", stop_after_first = true },
        javascript = { "prettierd", "prettier", stop_after_first = true },
        typescript = { "prettierd", "prettier", stop_after_first = true },
        javascriptreact = { "prettierd", "prettier", stop_after_first = true },
        typescriptreact = { "prettierd", "prettier", stop_after_first = true },

        -- JSON/YAML/Markdown (prettier handles these well)
        json = { "prettierd", "prettier", stop_after_first = true },
        yaml = { "prettierd", "prettier", stop_after_first = true },
        ["yaml.docker-compose"] = { "prettierd", "prettier", stop_after_first = true },
        ["yaml.gitlab"] = { "prettierd", "prettier", stop_after_first = true },

        markdown = { "prettierd", "prettier", stop_after_first = true },

        -- Shell scripts
        sh = { "shfmt" },
        bash = { "shfmt" },
        zsh = { "shfmt" },

        -- Dockerfile
        dockerfile = { "dockerfmt" },

        -- Rust (use rustfmt via LSP as fallback)
        rust = { "rustfmt", lsp_format = "fallback" },
      },
      -- Configure prettier to handle yaml subtypes as yaml
      formatters = {
        prettier = {
          options = {
            ft_parsers = {
              ["yaml.docker-compose"] = "yaml",
              ["yaml.gitlab"] = "yaml",
            },
          },
        },
        prettierd = {
          options = {
            ft_parsers = {
              ["yaml.docker-compose"] = "yaml",
              ["yaml.gitlab"] = "yaml",
            },
          },
        },
      },
      format_on_save = {
        timeout_ms = 500,
        lsp_format = "fallback",
      },
    })
    -- No need for manual BufWritePre autocmd - format_on_save handles it
  end,
}
