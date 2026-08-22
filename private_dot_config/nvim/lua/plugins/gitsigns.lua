require("gitsigns").setup({
  signs = {
    add = { text = "┃" },
    change = { text = "┃" },
    delete = { text = "_" },
    topdelete = { text = "‾" },
    changedelete = { text = "~" },
    untracked = { text = "┆" },
  },
  signs_staged = {
    add = { text = "┃" },
    change = { text = "┃" },
    delete = { text = "_" },
    topdelete = { text = "‾" },
    changedelete = { text = "~" },
    untracked = { text = "┆" },
  },
  current_line_blame = false,
  current_line_blame_opts = { delay = 1000 },
  current_line_blame_formatter = "<author>, <author_time:%R> - <summary>",
  on_attach = function(bufnr)
    local gitsigns = require("gitsigns")
    local map = function(keys, action, desc)
      vim.keymap.set("n", keys, action, { buffer = bufnr, desc = "Git: " .. desc })
    end

    map("]h", function()
      gitsigns.nav_hunk("next")
    end, "Next hunk")
    map("[h", function()
      gitsigns.nav_hunk("prev")
    end, "Previous hunk")
    map("<leader>gp", gitsigns.preview_hunk, "Preview hunk")
    map("<leader>gb", function()
      gitsigns.blame_line({ full = true })
    end, "Blame line")
    map("<leader>gB", gitsigns.toggle_current_line_blame, "Toggle line blame")
  end,
})
