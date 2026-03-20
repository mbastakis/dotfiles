-- Chezmoi template support
-- Provides filetype detection and Go template syntax highlighting for chezmoi source files
-- Strips chezmoi prefixes (dot_, private_, encrypted_, etc.) and .tmpl suffix
-- to set the correct base filetype for LSP and treesitter, then overlays
-- Go template syntax highlighting for {{ }} directives

return {
  {
    "alker0/chezmoi.vim",
    lazy = false,
    init = function()
      -- Use a temp buffer to avoid writing directly to source state
      vim.g["chezmoi#use_tmp_buffer"] = true
    end,
  },
}
