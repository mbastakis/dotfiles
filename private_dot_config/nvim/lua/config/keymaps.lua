-- Global keymaps
-- Most plugin-specific keymaps live in the plugin files in lua/plugins/

-- Window navigation
vim.keymap.set("n", "<C-h>", "<C-w>h", { desc = "Move to left window" })
vim.keymap.set("n", "<C-j>", "<C-w>j", { desc = "Move to bottom window" })
vim.keymap.set("n", "<C-k>", "<C-w>k", { desc = "Move to top window" })
vim.keymap.set("n", "<C-l>", "<C-w>l", { desc = "Move to right window" })

-- Save file (works in normal and insert mode)
vim.keymap.set("n", "<C-s>", "<cmd>w<CR>", { desc = "Save file" })
vim.keymap.set("i", "<C-s>", "<Esc><cmd>w<CR>a", { desc = "Save file and return to insert mode" })

-- Format buffer manually
vim.keymap.set("n", "<leader>fm", function()
  require("conform").format({ async = true, lsp_fallback = true })
end, { desc = "Format buffer" })

-- Diffview
local function is_git_repo()
  vim.fn.system({ "git", "rev-parse", "--is-inside-work-tree" })
  return vim.v.shell_error == 0
end

local function default_base_branch()
  local origin_head = vim.fn.systemlist({ "git", "symbolic-ref", "refs/remotes/origin/HEAD" })
  if vim.v.shell_error == 0 and #origin_head > 0 then
    return origin_head[1]:gsub("^refs/remotes/", "")
  end

  for _, branch in ipairs({ "main", "master" }) do
    vim.fn.system({ "git", "show-ref", "--verify", "--quiet", "refs/heads/" .. branch })
    if vim.v.shell_error == 0 then
      return branch
    end

    vim.fn.system({ "git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/" .. branch })
    if vim.v.shell_error == 0 then
      return "origin/" .. branch
    end
  end

  return nil
end

local function diffview_open(range)
  if not is_git_repo() then
    vim.notify("Not a git repository", vim.log.levels.WARN)
    return
  end

  local cmd = { cmd = "DiffviewOpen" }
  if range and range ~= "" then
    cmd.args = { range }
  end

  vim.api.nvim_cmd(cmd, {})
end

local function diffview_branch_vs_base()
  if not is_git_repo() then
    vim.notify("Not a git repository", vim.log.levels.WARN)
    return
  end

  local base = default_base_branch()
  if not base then
    vim.notify("Could not determine base branch", vim.log.levels.WARN)
    return
  end

  diffview_open(base .. "...HEAD")
end

local function diffview_pick_branch()
  if not is_git_repo() then
    vim.notify("Not a git repository", vim.log.levels.WARN)
    return
  end

  local ok, builtin = pcall(require, "telescope.builtin")
  if not ok then
    vim.notify("telescope.nvim not available", vim.log.levels.WARN)
    return
  end

  local themes = require("telescope.themes")

  builtin.git_branches(themes.get_dropdown({
    prompt_title = "Diff vs branch",
    attach_mappings = function(prompt_bufnr)
      local actions = require("telescope.actions")
      local action_state = require("telescope.actions.state")

      actions.select_default:replace(function()
        actions.close(prompt_bufnr)
        local selection = action_state.get_selected_entry()
        if not selection or not selection.value then
          return
        end

        local target = selection.value:gsub("^remotes/", "")
        target = target:gsub("%s+->.*$", "")
        if target == "" or target == "HEAD" or target:match("/HEAD$") then
          vim.notify("Select a branch (not HEAD)", vim.log.levels.WARN)
          return
        end

        diffview_open(target .. "...HEAD")
      end)

      return true
    end,
  }))
end

vim.keymap.set("n", "<leader>gd", diffview_branch_vs_base, { desc = "Diffview: branch vs base" })
vim.keymap.set("n", "<leader>gD", diffview_pick_branch, { desc = "Diffview: branch vs picked" })
vim.keymap.set("n", "<leader>gm", function()
  diffview_open()
end, { desc = "Diffview: open (index/merge)" })
vim.keymap.set("n", "<leader>gq", "<cmd>DiffviewClose<CR>", { desc = "Diffview: close" })

local function set_diffview_buffer_keymaps(bufnr)
  local opts = { buffer = bufnr, desc = "Diffview: toggle files" }
  vim.keymap.set("n", "<C-_>", "<cmd>DiffviewToggleFiles<CR>", opts)
  vim.keymap.set("n", "<C-/>", "<cmd>DiffviewToggleFiles<CR>", opts)
end

vim.api.nvim_create_autocmd("User", {
  pattern = "DiffviewViewOpened",
  callback = function()
    for _, win in ipairs(vim.api.nvim_tabpage_list_wins(0)) do
      set_diffview_buffer_keymaps(vim.api.nvim_win_get_buf(win))
    end
  end,
})
