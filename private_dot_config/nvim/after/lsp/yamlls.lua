-- Override yamlls to NOT attach to docker-compose files
-- docker_compose_language_service handles docker-compose files
-- Also configure GitLab CI schema support

vim.lsp.config('yamlls', {
  on_attach = function(client, bufnr)
    local fname = vim.api.nvim_buf_get_name(bufnr)
    -- Stop yamlls if this is a docker-compose file
    if fname:match('docker%-compose%.ya?ml$') or fname:match('compose%.ya?ml$') then
      vim.lsp.stop_client(client.id)
      return false
    end
  end,
  settings = {
    yaml = {
      format = {
        enable = true,
      },
      -- Schema store configuration
      schemaStore = {
        enable = true,
        url = "https://www.schemastore.org/api/json/catalog.json",
      },
      -- GitLab CI schema mapping
      schemas = {
        ["https://gitlab.com/gitlab-org/gitlab/-/raw/master/app/assets/javascripts/editor/schema/ci.json"] = {
          ".gitlab-ci.yml",
          ".gitlab-ci.yaml",
          "**/.gitlab-ci.yml",
          "**/.gitlab-ci.yaml",
        },
      },
    },
    redhat = {
      telemetry = {
        enabled = false,
      },
    },
  },
})
