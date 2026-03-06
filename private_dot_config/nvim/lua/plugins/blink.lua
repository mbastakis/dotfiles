return {
  "saghen/blink.cmp",
  dependencies = {
    "rafamadriz/friendly-snippets",
    "supermaven-inc/supermaven-nvim",
    "Huijiro/blink-cmp-supermaven",
    -- blink.compat provides a fake "cmp" module so supermaven-nvim's
    -- require("cmp") check passes and doesn't warn about missing nvim-cmp.
    { "saghen/blink.compat", version = "1.*", opts = {} },
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
          score_offset = 100,
          async = true,
          transform_items = function(_, items)
            for _, item in ipairs(items) do
              item.source_name = "supermaven"
              item.kind_icon = "󰧑"
              item.kind_name = "Supermaven"
            end
            return items
          end,
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
