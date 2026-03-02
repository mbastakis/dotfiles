return {
  "saghen/blink.cmp",
  dependencies = {
    "rafamadriz/friendly-snippets",
    "supermaven-inc/supermaven-nvim",
    "Huijiro/blink-cmp-supermaven",
  },

  version = "1.*",
  -- @module 'blink.cmp'
  -- @type blink.cmp.Config
  opts = {
    keymap = { preset = "default" },

    appearance = {
      nerd_font_variant = "mono",
    },
    completion = { documentation = { auto_show = false } },
    sources = {
      default = { "supermaven", "lsp", "path", "snippets", "buffer" },
      per_filetype = {
        codecompanion = { "codecompanion", "buffer" },
      },
      providers = {
        supermaven = {
          name = "supermaven",
          module = "blink-cmp-supermaven",
          async = true,
          score_offset = 100,
        },
        codecompanion = {
          name = "CodeCompanion",
          module = "codecompanion.providers.completion.blink",
          enabled = true,
        },
      },
    },

    fuzzy = { implementation = "prefer_rust_with_warning" },
  },
  opts_extend = { "sources.default" },
}
