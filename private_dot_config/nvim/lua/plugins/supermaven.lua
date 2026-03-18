return {
  "supermaven-inc/supermaven-nvim",
  event = "InsertEnter",
  opts = {
    keymaps = {
      accept_suggestion = "<Tab>",
      accept_word = "<C-g>",
      clear_suggestion = "<C-]>",
    },
    ignore_filetypes = { "codecompanion" },
    log_level = "info",
    disable_inline_completion = false,
    disable_keymaps = false,
  },
}
