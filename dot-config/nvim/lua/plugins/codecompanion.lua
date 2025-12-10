return {
  "olimorris/codecompanion.nvim",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "nvim-treesitter/nvim-treesitter",
  },
  config = function()
    require("codecompanion").setup({
      strategies = {
        chat = {
          adapter = "opencode",
        },
      },
      ignore_warnings = true,
    })
    -- Keymaps
    vim.keymap.set({ "n", "v" }, "<leader>ap", "<cmd>CodeCompanionActions<cr>", { desc = "CodeCompanion Actions" })
    vim.keymap.set({ "n", "v" }, "<leader>ac", "<cmd>CodeCompanionChat Toggle<cr>", { desc = "Toggle AI Chat" })
  end,
}
