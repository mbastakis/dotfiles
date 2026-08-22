local conform = require("conform")

conform.setup({
  formatters_by_ft = {
    dockerfile = { "dockerfmt" },
    javascript = { "prettierd", "prettier", stop_after_first = true },
    javascriptreact = { "prettierd", "prettier", stop_after_first = true },
    python = { "ruff_format" },
    terraform = { "tofu_fmt" },
    ["terraform-vars"] = { "tofu_fmt" },
    toml = { "taplo" },
    typescript = { "prettierd", "prettier", stop_after_first = true },
    typescriptreact = { "prettierd", "prettier", stop_after_first = true },
    ["yaml.docker-compose"] = { "prettierd", "prettier", stop_after_first = true },
  },
  format_on_save = function(bufnr)
    if vim.bo[bufnr].filetype == "helm" then
      return
    end
    return { lsp_format = "fallback", timeout_ms = 5000 }
  end,
  formatters = {
    prettier = { options = { ft_parsers = { ["yaml.docker-compose"] = "yaml" } } },
    prettierd = { options = { ft_parsers = { ["yaml.docker-compose"] = "yaml" } } },
  },
})

vim.keymap.set("n", "<leader>fm", function()
  if vim.bo.filetype == "helm" then
    vim.notify("Formatting is disabled for Helm templates", vim.log.levels.INFO)
    return
  end
  conform.format({ async = true, lsp_format = "fallback" })
end, { desc = "Format buffer" })
