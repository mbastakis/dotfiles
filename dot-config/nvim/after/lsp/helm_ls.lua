-- Helm LSP configuration
-- helm_ls defaults: filetypes: { 'helm', 'yaml.helm-values' }, root_markers: { 'Chart.yaml' }
-- This file extends the defaults with custom settings for better Helm template support
-- Documentation: https://github.com/mrjosh/helm-ls

vim.lsp.config("helm_ls", {
  settings = {
    ["helm-ls"] = {
      logLevel = "info",
      valuesFiles = {
        mainValuesFile = "values.yaml",
        lintOverlayValuesFile = "values.lint.yaml",
        additionalValuesFilesGlobPattern = "*values*.yaml",
      },
      yamlls = {
        enabled = true,
        enabledForFilesGlob = "*.{yaml,yml}",
        diagnosticsLimit = 50,
        showDiagnosticsDirectly = false,
        path = "yaml-language-server",
        config = {
          schemas = {
            kubernetes = "templates/**",
          },
          completion = true,
          hover = true,
        },
      },
    },
  },
})
