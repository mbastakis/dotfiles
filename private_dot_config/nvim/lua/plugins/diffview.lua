return {
  "sindrets/diffview.nvim",
  cmd = {
    "DiffviewOpen",
    "DiffviewClose",
    "DiffviewToggleFiles",
    "DiffviewFocusFiles",
    "DiffviewRefresh",
    "DiffviewFileHistory",
  },
  dependencies = { "nvim-lua/plenary.nvim" },
  opts = {
    enhanced_diff_hl = true,
  },
}
