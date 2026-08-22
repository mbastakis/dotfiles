local lint = require("lint")

lint.linters_by_ft = {
  bash = { "shellcheck" },
  dockerfile = { "hadolint" },
  javascript = { "eslint_d" },
  javascriptreact = { "eslint_d" },
  python = { "ruff" },
  sh = { "shellcheck" },
  terraform = { "tflint", "tfsec" },
  ["terraform-vars"] = { "tflint" },
  typescript = { "eslint_d" },
  typescriptreact = { "eslint_d" },
  yaml = { "yamllint" },
  ["yaml.docker-compose"] = { "yamllint" },
}

local function try_lint()
  local linters = lint.linters_by_ft[vim.bo.filetype]
  if not linters then
    return
  end

  for _, name in ipairs(linters) do
    local linter = lint.linters[name]
    local cmd = type(linter.cmd) == "function" and linter.cmd() or linter.cmd
    if vim.fn.executable(cmd) == 1 then
      local opts
      if name == "tflint" then
        local root = vim.fs.root(0, { ".tflint.hcl", ".terraform", ".git" })
        opts = root and { cwd = root } or nil
      end
      lint.try_lint(name, opts)
    end
  end
end

vim.api.nvim_create_autocmd({ "BufReadPost", "BufWritePost" }, {
  group = vim.api.nvim_create_augroup("native-lint", { clear = true }),
  callback = try_lint,
})
