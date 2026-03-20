-- Go / Go template LSP configuration
-- Extends gopls to handle gotmpl filetype for chezmoi .tmpl and Go template files
-- gopls provides completion for Go template functions and basic diagnostics
-- Documentation: https://pkg.go.dev/golang.org/x/tools/gopls

vim.lsp.config("gopls", {
  filetypes = { "go", "gomod", "gowork", "gotmpl" },
})
