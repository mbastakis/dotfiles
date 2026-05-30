return {
  "iamcco/markdown-preview.nvim",
  cmd = { "MarkdownPreview", "MarkdownPreviewStop", "MarkdownPreviewToggle" },
  ft = { "markdown" },
  build = "cd app && npx --yes yarn install --frozen-lockfile",
  keys = {
    { "<leader>m", "<cmd>MarkdownPreviewToggle<cr>", desc = "Markdown Preview" },
  },
  init = function()
    vim.g.mkdp_filetypes = { "markdown" }
    vim.g.mkdp_auto_start = 0
    vim.g.mkdp_auto_close = 0
    vim.g.mkdp_refresh_slow = 1
    vim.g.mkdp_theme = "dark"
  end,
}
