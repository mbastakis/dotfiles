return {
  "saghen/blink.cmp",
  dependencies = { "rafamadriz/friendly-snippets" },

  version = "1.*",
  -- @module 'blink.cmp'
  -- @type blink.cmp.Config
  opts = {
    keymap = { preset = "default" },

    appearance = {
      nerd_font_variant = "mono",
    },
    completion = { documentation = { auto_show = false } },
    providers = {
      codecompanion = {
        name = "CodeCompanion",
        module = "codecompanion.providers.completion.blink",
        enabled = true,
      },
    },
    sources = {
      default = { "lsp", "path", "snippets", "buffer" },
      per_filetype = {
        codecompanion = { "codecompanion", "buffer" },
      },
    },

    fuzzy = { implementation = "prefer_rust_with_warning" },
  },
  opts_extend = { "sources.default" },
}
