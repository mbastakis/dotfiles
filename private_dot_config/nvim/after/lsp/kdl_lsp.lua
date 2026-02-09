-- Install manually: cargo install kdl-lsp
vim.lsp.config("kdl_lsp", {
  cmd = { "kdl-lsp" },
  filetypes = { "kdl" },
})

if vim.fn.executable("kdl-lsp") == 1 then
  vim.lsp.enable("kdl_lsp")
end
