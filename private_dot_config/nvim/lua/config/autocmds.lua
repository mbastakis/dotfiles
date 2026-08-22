vim.api.nvim_create_autocmd("TextYankPost", {
  desc = "Highlight yanked text",
  group = vim.api.nvim_create_augroup("highlight-yank", { clear = true }),
  callback = function()
    vim.hl.on_yank()
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  desc = "Enable Tree-sitter highlighting when a parser is available",
  group = vim.api.nvim_create_augroup("treesitter-highlight", { clear = true }),
  callback = function(event)
    pcall(vim.treesitter.start, event.buf)
  end,
})
