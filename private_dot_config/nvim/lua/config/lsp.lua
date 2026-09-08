vim.filetype.add({
  extension = { gotmpl = "gotmpl" },
  filename = {
    ["docker-compose.yml"] = "yaml.docker-compose",
    ["docker-compose.yaml"] = "yaml.docker-compose",
    ["compose.yml"] = "yaml.docker-compose",
    ["compose.yaml"] = "yaml.docker-compose",
  },
  pattern = {
    ["docker%-compose%..*%.ya?ml"] = "yaml.docker-compose",
    [".*/templates/.*%.ya?ml"] = function(path)
      return vim.fs.root(path, { "Chart.yaml" }) and "helm" or "yaml"
    end,
    [".*/templates/.*%.tpl"] = function(path)
      if vim.fs.root(path, { "Chart.yaml" }) then
        return "helm"
      end
    end,
  },
})

vim.treesitter.language.register("yaml", "yaml.docker-compose")
vim.treesitter.language.register("gotmpl", "helm")

vim.diagnostic.config({
  severity_sort = true,
  update_in_insert = false,
  virtual_text = true,
  float = { border = "rounded", source = true },
})

vim.lsp.config("*", {
  capabilities = require("blink.cmp").get_lsp_capabilities(),
})

-- Display hints by default for every server that supports them.
vim.lsp.inlay_hint.enable(true)

vim.lsp.config("lua_ls", {
  settings = {
    Lua = {
      hint = { enable = true },
    },
  },
})

vim.lsp.config("gopls", {
  settings = {
    gopls = {
      analyses = { unusedparams = true },
      staticcheck = true,
      hints = {
        assignVariableTypes = true,
        compositeLiteralFields = true,
        compositeLiteralTypes = true,
        constantValues = true,
        functionTypeParameters = true,
        ignoredError = true,
        parameterNames = true,
        rangeVariableTypes = true,
      },
    },
  },
})

vim.lsp.config("yamlls", {
  filetypes = { "yaml" },
})

vim.lsp.config("helm_ls", {
  settings = {
    ["helm-ls"] = {
      valuesFiles = {
        mainValuesFile = "values.yaml",
        lintOverlayValuesFile = "values.lint.yaml",
        additionalValuesFilesGlobPattern = "*values*.yaml",
      },
      yamlls = {
        enabled = true,
        path = "yaml-language-server",
        config = {
          schemas = { kubernetes = "templates/**" },
          completion = true,
          hover = true,
        },
      },
    },
  },
})

vim.api.nvim_create_autocmd("LspAttach", {
  group = vim.api.nvim_create_augroup("native-lsp", { clear = true }),
  callback = function(event)
    local client = vim.lsp.get_client_by_id(event.data.client_id)
    if client and client:supports_method("textDocument/foldingRange") then
      for _, win in ipairs(vim.fn.win_findbuf(event.buf)) do
        vim.wo[win].foldexpr = "v:lua.vim.lsp.foldexpr()"
        vim.wo[win].foldtext = "v:lua.vim.lsp.foldtext()"
      end
    end

    local map = function(keys, func, desc)
      vim.keymap.set("n", keys, func, { buffer = event.buf, desc = "LSP: " .. desc })
    end

    map("gd", vim.lsp.buf.definition, "Go to definition")
    map("gD", vim.lsp.buf.declaration, "Go to declaration")
    map("gr", vim.lsp.buf.references, "Go to references")
    map("gI", vim.lsp.buf.implementation, "Go to implementation")
    map("gy", vim.lsp.buf.type_definition, "Go to type definition")
    map("K", vim.lsp.buf.hover, "Hover documentation")
    map("<leader>ca", vim.lsp.buf.code_action, "Code action")
    map("<leader>rn", vim.lsp.buf.rename, "Rename symbol")
    map("<leader>d", vim.diagnostic.open_float, "Show line diagnostics")
    map("<leader>q", vim.diagnostic.setloclist, "Open diagnostics list")
    map("<leader>h", function()
      local filter = { bufnr = event.buf }
      vim.lsp.inlay_hint.enable(not vim.lsp.inlay_hint.is_enabled(filter), filter)
    end, "Toggle inlay hints")
  end,
})

local servers = {
  bashls = "bash-language-server",
  docker_language_server = "docker-language-server",
  gopls = "gopls",
  helm_ls = "helm_ls",
  jsonls = "vscode-json-language-server",
  lua_ls = "lua-language-server",
  pyright = "pyright-langserver",
  taplo = "taplo",
  terraformls = "terraform-ls",
  tsc = "tsc",
  yamlls = "yaml-language-server",
}

for server, executable in pairs(servers) do
  if vim.fn.executable(executable) == 1 then
    vim.lsp.enable(server)
  end
end
