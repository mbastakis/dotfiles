return {
  "mfussenegger/nvim-lint",
  event = { "BufReadPre", "BufNewFile" },
  config = function()
    local lint = require("lint")

    -- Configure linters by filetype (using linters installed via Mason)
    lint.linters_by_ft = {
      -- Lua
      lua = { "selene" },

      -- Python (ruff is faster, pylint is more thorough)
      python = { "ruff" },

      -- HTML
      html = { "htmlhint" },

      -- CSS/SCSS/Less
      css = { "stylelint" },
      scss = { "stylelint" },
      less = { "stylelint" },

      -- JavaScript/TypeScript
      javascript = { "eslint_d" },
      typescript = { "eslint_d" },
      javascriptreact = { "eslint_d" },
      typescriptreact = { "eslint_d" },

      -- Markdown
      markdown = { "markdownlint" },

      -- Shell scripts
      sh = { "shellcheck" },
      bash = { "shellcheck" },
      zsh = { "shellcheck" },

      -- YAML
      yaml = { "yamllint" },
      ["yaml.gitlab"] = { "yamllint" },

      -- JSON
      json = { "jsonlint" },

      -- Docker
      dockerfile = { "hadolint" },

      -- Docker Compose (yamllint + docker-compose LSP diagnostics)
      ["yaml.docker-compose"] = { "yamllint" },
    }

    -- Create autocommand to trigger linting
    local lint_augroup = vim.api.nvim_create_augroup("lint", { clear = true })

    vim.api.nvim_create_autocmd({ "BufEnter", "BufWritePost", "InsertLeave" }, {
      group = lint_augroup,
      callback = function()
        lint.try_lint()
      end,
    })
  end,
}
