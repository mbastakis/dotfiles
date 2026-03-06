return {
  "supermaven-inc/supermaven-nvim",
  event = "InsertEnter",
  opts = {
    keymaps = {
      accept_suggestion = nil, -- handled by blink.cmp
    },
    ignore_filetypes = { "codecompanion" },
    log_level = "info",
    disable_inline_completion = true,
    disable_keymaps = true,
  },
}
