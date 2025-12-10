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
      ignore_warnings = true,
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
