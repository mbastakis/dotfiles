return {
  "MeanderingProgrammer/render-markdown.nvim",
  ft = { "markdown", "codecompanion" },
  dependencies = {
    "nvim-treesitter/nvim-treesitter",
  },
  opts = {
    file_types = { "markdown", "codecompanion" },
    heading = {
      backgrounds = {
        "RenderMarkdownH1Bg",
        "RenderMarkdownH2Bg",
        "RenderMarkdownH3Bg",
        "RenderMarkdownH4Bg",
        "RenderMarkdownH5Bg",
        "RenderMarkdownH6Bg",
      },
    },
    code = {
      width = "block",
      right_pad = 2,
    },
    bullet = {
      icons = { "●", "○", "◆", "◇" },
    },
    checkbox = {
      unchecked = { icon = "󰄱 " },
      checked = { icon = "󰄵 " },
    },
  },
}
