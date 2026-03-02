return {
  "supermaven-inc/supermaven-nvim",
  event = "InsertEnter",
  opts = {
    ignore_filetypes = { "codecompanion" },
    log_level = "info",
    disable_inline_completion = true,
    disable_keymaps = true,
  },
}
