require("supermaven-nvim").setup({
  keymaps = {
    accept_suggestion = "<Tab>",
    accept_word = "<C-g>",
    clear_suggestion = "<C-]>",
  },
  log_level = "info",
  disable_inline_completion = false,
  disable_keymaps = false,
})

vim.keymap.set("n", "<leader>ua", require("supermaven-nvim.api").toggle, { desc = "Toggle Supermaven" })
