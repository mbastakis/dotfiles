-- Autocommands

local autocmd = vim.api.nvim_create_autocmd
local augroup = vim.api.nvim_create_augroup

-- Highlight when yanking (copying) text
autocmd("TextYankPost", {
  desc = "Highlight when yanking (copying) text",
  group = augroup("highlight-yank", { clear = true }),
  callback = function()
    vim.hl.on_yank()
  end,
})

-- Detect Helm template files and set filetype to 'helm'
autocmd({ "BufRead", "BufNewFile" }, {
  desc = "Detect Helm template files in templates/ directories",
  group = augroup("helm-filetype", { clear = true }),
  pattern = { "*/templates/*.yaml", "*/templates/*.tpl", "*/templates/*.yml" },
  callback = function()
    -- Check if we're in a Helm chart directory (contains Chart.yaml)
    local chart_file = vim.fs.find("Chart.yaml", {
      upward = true,
      path = vim.fn.expand("%:p:h"),
    })[1]

    if chart_file then
      vim.bo.filetype = "helm"
    end
  end,
})

-- Enable treesitter highlighting and indentation for all filetypes
autocmd("FileType", {
  desc = "Enable treesitter highlighting and indentation",
  group = augroup("treesitter-features", { clear = true }),
  callback = function()
    if pcall(vim.treesitter.start) then
      vim.bo.indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
    end
  end,
})
