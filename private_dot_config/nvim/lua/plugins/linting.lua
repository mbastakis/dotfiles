return {
  "mfussenegger/nvim-lint",
  event = { "BufReadPre", "BufNewFile" },
  config = function()
    local lint = require("lint")

    -- Custom Helm linter
    lint.linters.helm_lint = {
      cmd = "helm",
      stdin = false,
      args = { "lint", "." },
      stream = "stdout",
      ignore_exitcode = true,
      parser = function(output, bufnr)
        local diagnostics = {}
        local chart_root = vim.fn.fnamemodify(vim.api.nvim_buf_get_name(bufnr), ":h")
        
        -- Find the chart root (directory containing Chart.yaml)
        while chart_root ~= "/" do
          if vim.fn.filereadable(chart_root .. "/Chart.yaml") == 1 then
            break
          end
          chart_root = vim.fn.fnamemodify(chart_root, ":h")
        end

        for line in output:gmatch("[^\r\n]+") do
          -- Match: [ERROR] templates/: file:line:col
          local severity, file, lnum, col, message = line:match("%[(%w+)%]%s+(.-):(.-):(.-)%s+(.+)")
          
          if not severity then
            -- Match: [ERROR] file: message (without line number)
            severity, file, message = line:match("%[(%w+)%]%s+(.-):%s+(.+)")
            lnum, col = "1", "1"
          end

          if severity and file and message then
            -- Only show diagnostics for the current buffer's file
            local current_file = vim.api.nvim_buf_get_name(bufnr)
            local diagnostic_file = chart_root .. "/" .. file
            
            -- If this diagnostic is for the current file or it's a general chart error
            if current_file:match(file:gsub("%-", "%%-")) or file == "Chart.yaml" or file:match("^templates/") then
              table.insert(diagnostics, {
                lnum = tonumber(lnum) and (tonumber(lnum) - 1) or 0,
                col = tonumber(col) and (tonumber(col) - 1) or 0,
                message = message,
                severity = severity == "ERROR" and vim.diagnostic.severity.ERROR
                  or severity == "WARNING" and vim.diagnostic.severity.WARN
                  or vim.diagnostic.severity.INFO,
                source = "helm",
              })
            end
          end
        end

        return diagnostics
      end,
    }

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

      -- Helm templates - use helm lint for validation
      helm = { "helm_lint" },

      -- JSON
      json = { "jsonlint" },

      -- Docker
      dockerfile = { "hadolint" },

      -- Docker Compose (yamllint + docker-compose LSP diagnostics)
      ["yaml.docker-compose"] = { "yamllint" },

      -- Nix
      nix = { "statix" },

      -- Go
      go = { "golangcilint" },

      -- Terraform
      terraform = { "tflint", "tfsec" },
      ["terraform-vars"] = { "tflint" },
    }

    -- Create autocommand to trigger linting
    local lint_augroup = vim.api.nvim_create_augroup("lint", { clear = true })

    vim.api.nvim_create_autocmd({ "BufEnter", "BufWritePost", "InsertLeave" }, {
      group = lint_augroup,
      callback = function()
        -- For YAML files in Helm charts, use helm lint instead of yamllint
        if vim.bo.filetype == "yaml" then
          local filepath = vim.api.nvim_buf_get_name(0)
          local chart_file = vim.fs.find("Chart.yaml", {
            upward = true,
            path = vim.fs.dirname(filepath),
          })[1]
          
          if chart_file then
            -- This is a YAML file in a Helm chart, use helm_lint
            lint.try_lint("helm_lint")
            return
          end
        end
        
        -- Default linting behavior
        lint.try_lint()
      end,
    })
  end,
}
