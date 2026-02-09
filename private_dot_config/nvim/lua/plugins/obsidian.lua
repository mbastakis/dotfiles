return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  event = "BufReadPre */Documents/notes/*.md",
  dependencies = { "nvim-telescope/telescope.nvim" },
  opts = {
    legacy_commands = false,
    ui = { enable = false },
    workspaces = {
      {
        name = "notes",
        path = "~/Documents/notes",
      },
    },
  },
  keys = {
    { "<leader>on", "<cmd>Obsidian new<cr>", desc = "Obsidian new note" },
    { "<leader>os", "<cmd>Obsidian search<cr>", desc = "Obsidian search" },
    { "<leader>ot", "<cmd>Obsidian today<cr>", desc = "Obsidian today" },
  },
}
