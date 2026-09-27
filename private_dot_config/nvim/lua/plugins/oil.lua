require("oil").setup({
  columns = {},
  win_options = { signcolumn = "yes:2" },
  constrain_cursor = "editable",
  lsp_file_methods = {
    enabled = true,
    timeout_ms = 1000,
    autosave_changes = false,
  },
  watch_for_changes = true,
  keymaps = {
    ["<C-p>"] = "actions.preview",
    ["gx"] = "actions.open_external",
  },
  view_options = {
    show_hidden = true,
    natural_order = "fast",
    sort = {
      { "type", "asc" },
      { "name", "asc" },
    },
  },
})

require("oil-git-status").setup({})
