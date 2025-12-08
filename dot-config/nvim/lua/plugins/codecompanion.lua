return {
  "olimorris/codecompanion.nvim",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "nvim-treesitter/nvim-treesitter",
  },
  opts = {
    opts = {
      log_level = "DEBUG",
    },
  },
  config = function()
    require("codecompanion").setup({
      strategies = {
        chat = {
          adapter = {
            name = "opencode",
            model = "claude-sonnet-4",
          },
        },
      },
    })
  end,
}
