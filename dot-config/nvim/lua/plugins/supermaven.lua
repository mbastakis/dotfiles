return {
  "supermaven-inc/supermaven-nvim",
  event = "InsertEnter",
  opts = {
    keymaps = {
      accept_suggestion = "<Tab>",
      clear_suggestion = "<C-]>",
      accept_word = "<C-j>",
    },
    ignore_filetypes = { "codecompanion" },
    color = {
      suggestion_color = "#585b70", -- Catppuccin overlay0
      cterm = 244,
    },
    log_level = "info",
    disable_inline_completion = false,
    disable_keymaps = false,
  },
}
