require("blink.cmp").setup({
  keymap = { preset = "default" },
  appearance = { nerd_font_variant = "mono" },
  completion = { documentation = { auto_show = false } },
  sources = {
    default = { "lsp", "path", "snippets", "buffer", "ripgrep" },
    providers = {
      ripgrep = {
        name = "Ripgrep",
        module = "blink-ripgrep",
        opts = { prefix_min_len = 3 },
      },
    },
  },
  fuzzy = { implementation = "prefer_rust_with_warning" },
})
