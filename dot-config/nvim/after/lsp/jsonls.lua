vim.lsp.config("jsonls", {
  filetypes = { "json", "jsonc" },
  settings = {
    json = {
      validate = { enable = true },
    },
  },
})
