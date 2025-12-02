vim.g.maplocalleader = " "
vim.g.mapleader = " "

vim.g.have_nerd_font = true

vim.o.number = true
vim.o.relativenumber = true
vim.o.winborder = "rounded"

vim.o.mouse = "a"
vim.o.showmode = false

vim.schedule(function()
  vim.o.clipboard = "unnamedplus"
end)

vim.o.undofile = true

vim.o.ignorecase = true
vim.o.smartcase = true

vim.o.signcolumn = "yes"
vim.o.updatetime = 250
vim.o.timeoutlen = 300

-- Configure how new splits should be opened
vim.o.splitright = true
vim.o.splitbelow = true

vim.o.list = true
vim.opt.listchars = { tab = "» ", trail = "·", nbsp = "␣" }
vim.o.inccommand = "split"
vim.o.cursorline = true
vim.o.scrolloff = 10
vim.o.confirm = true
vim.o.breakindent = true
vim.cmd("set expandtab")
vim.cmd("set tabstop=2")
vim.cmd("set softtabstop=2")
vim.cmd("set shiftwidth=2")

-- Custom filetype mappings
vim.filetype.add({
  filename = {
    ["docker-compose.yml"] = "yaml.docker-compose",
    ["docker-compose.yaml"] = "yaml.docker-compose",
    ["compose.yml"] = "yaml.docker-compose",
    ["compose.yaml"] = "yaml.docker-compose",
    [".gitlab-ci.yml"] = "yaml.gitlab",
    [".gitlab-ci.yaml"] = "yaml.gitlab",
  },
  pattern = {
    ["docker%-compose%..*%.ya?ml"] = "yaml.docker-compose", -- docker-compose.*.yml or docker-compose.*.yaml
    [".*%.gitlab%-ci%.ya?ml"] = "yaml.gitlab", -- *.gitlab-ci.yml or *.gitlab-ci.yaml
    [".*/templates/.*%.ya?ml"] = function(path, bufnr)
      -- Check if we're in a Helm chart (has Chart.yaml in parent dirs)
      if vim.fs.root(path, { "Chart.yaml" }) then
        return "helm"
      end
      return "yaml"
    end,
    [".*/templates/.*%.tpl"] = function(path, bufnr)
      -- Check if we're in a Helm chart (has Chart.yaml in parent dirs)
      if vim.fs.root(path, { "Chart.yaml" }) then
        return "helm"
      end
    end,
  },
})
