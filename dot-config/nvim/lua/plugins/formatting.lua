return {
  "stevearc/conform.nvim",
  opts = {},
  config = function()
    require("conform").setup({
      formatters_by_ft = {
        -- Lua
        lua = { "stylua" },

        -- Python (ruff handles both formatting and import sorting)
        python = { "ruff_format" },

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

        -- Helm templates - no formatting (Go templates break with prettier)
        helm = {},

        -- Shell scripts
        sh = { "shfmt" },
        bash = { "shfmt" },
        zsh = { "shfmt" },

        -- Dockerfile
        dockerfile = { "dockerfmt" },

        -- Nix
        nix = { "alejandra" },

        -- Rust (use rustfmt via LSP as fallback)
        rust = { "rustfmt", lsp_format = "fallback" },

        -- Go (gofumpt is stricter than gofmt, golines wraps long lines)
        go = { "gofumpt", "golines" },

        -- Terraform (use LSP's terraform fmt)
        terraform = { "terraform_fmt", lsp_format = "fallback" },

        -- TOML
        toml = { "taplo" },
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
        lsp_format = "fallback",
        timeout_ms = 2000,
      },
      format_after_save = {
        lsp_format = "fallback",
      },
      log_level = vim.log.levels.WARN, -- Reduce log noise
    })
  end,
}
