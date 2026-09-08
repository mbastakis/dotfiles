vim.pack.add({
  { src = "https://github.com/christoomey/vim-tmux-navigator" },
  { src = "https://github.com/folke/snacks.nvim" },
  { src = "https://github.com/kylechui/nvim-surround", version = vim.version.range("4.x") },
  { src = "https://github.com/lewis6991/gitsigns.nvim" },
  { src = "https://github.com/mfussenegger/nvim-lint" },
  { src = "https://github.com/neovim/nvim-lspconfig" },
  { src = "https://github.com/nvim-treesitter/nvim-treesitter" },
  { src = "https://github.com/nvim-mini/mini.pick", version = "stable" },
  { src = "https://github.com/rafamadriz/friendly-snippets" },
  { src = "https://github.com/saghen/blink.cmp", version = "v1" },
  { src = "https://github.com/stevearc/conform.nvim" },
  { src = "https://github.com/stevearc/oil.nvim" },
  { src = "https://github.com/supermaven-inc/supermaven-nvim" },
})

-- Enable only image previews; open diagrams manually with <leader>ip.
-- Preserve Ghostty detection through tmux so images stay anchored to the float.
if vim.env.GHOSTTY_RESOURCES_DIR and not vim.env.SNACKS_GHOSTTY then
  vim.env.SNACKS_GHOSTTY = "1"
end
require("snacks").setup({
  image = {
    enabled = true,
    doc = { inline = false, float = false },
    math = { enabled = false },
  },
  styles = {
    -- False offsets override the cursor-relative defaults with automatic centering.
    snacks_image = { relative = "editor", row = false, col = false },
  },
})

local preview_open = false
local function close_preview()
  if preview_open then
    Snacks.image.doc.hover_close()
    preview_open = false
  end
end

vim.keymap.set("n", "<leader>ip", function()
  if preview_open then
    close_preview()
  else
    preview_open = true
    -- Manual previews must wait for terminal detection, just like auto previews.
    -- Otherwise Ghostty can use absolute image placement instead of placeholders.
    Snacks.image.terminal.detect(function()
      if preview_open then
        Snacks.image.hover()
      end
    end)
  end
end, { desc = "Toggle centered image/diagram preview" })

vim.api.nvim_create_autocmd({ "CursorMoved", "InsertEnter", "BufLeave" }, {
  group = vim.api.nvim_create_augroup("image_preview", { clear = true }),
  callback = close_preview,
})
