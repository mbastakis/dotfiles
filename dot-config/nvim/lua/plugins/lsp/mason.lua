-- Mason: Package manager for LSP servers, DAP servers, linters, and formatters
-- mason-lspconfig: Bridge between mason.nvim and nvim-lspconfig
-- mason-tool-installer: Automatically install tools via Mason

return {
  -- Mason core
  {
    "mason-org/mason.nvim",
    opts = {
      ui = {
        icons = {
          package_installed = "✓",
          package_pending = "➜",
          package_uninstalled = "✗",
        },
      },
    },
  },

  -- Mason-lspconfig bridge
  {
    "mason-org/mason-lspconfig.nvim",
    dependencies = {
      "mason.nvim",
      "nvim-lspconfig",
    },
    opts = {
      -- Servers to auto-install if not present
      ensure_installed = {
        "lua_ls", -- Lua
        "ts_ls", -- TypeScript/JavaScript
        "html", -- HTML
        "cssls", -- CSS/SCSS/Less
        "eslint", -- ESLint
        "pyright", -- Python
        "gopls", -- Go
        "terraformls", -- Terraform
        "rust_analyzer", -- Rust
        "taplo", -- TOML (has LSP capabilities)
        "gitlab_ci_ls", -- GitLab CI
        "dockerls", -- Dockerfile
        "docker_compose_language_service", -- Docker Compose
        "yamlls", -- YAML
        "ansiblels", -- Ansible
      },
      automatic_enable = true,
    },
  },

  -- Mason tool installer (for formatters, linters, etc.)
  {
    "WhoIsSethDaniel/mason-tool-installer.nvim",
    dependencies = { "mason.nvim" },
    opts = {
      ensure_installed = {
        -- Formatters
        "prettier", -- JS/TS/HTML/CSS/JSON/YAML/Markdown formatter
        "prettierd", -- Faster prettier daemon
        "stylua", -- Lua formatter
        "black", -- Python formatter
        "isort", -- Python import sorter
        "shfmt", -- Shell script formatter
        "gofumpt", -- Go formatter (opinionated)
        "golines", -- Go line length formatter
        "nixpkgs-fmt", -- Nix formatter

        -- Linters
        "eslint_d", -- JS/TS linter (fast daemon)
        "stylelint", -- CSS/SCSS/Less linter
        "htmlhint", -- HTML linter
        "selene", -- Lua linter (modern, doesn't require luarocks)
        "shellcheck", -- Shell script linter
        "markdownlint", -- Markdown linter
        "pylint", -- Python linter
        "ruff", -- Fast Python linter
        "yamllint", -- YAML linter
        "jsonlint", -- JSON linter
        "hadolint", -- Dockerfile linter
        "golangci-lint", -- Go linter (comprehensive)
        "sqlfluff", -- SQL linter/formatter
        "ansible-lint", -- Ansible linter
        "checkmake", -- Makefile linter
        "dotenv-linter", -- .env file linter
        "cfn-lint", -- CloudFormation linter

        -- Terraform/IaC
        "tflint", -- Terraform linter
        "tfsec", -- Terraform security scanner

        -- CI/CD
        "actionlint", -- GitHub Actions workflow linter

        -- Security
        "trivy", -- Security scanner for containers/IaC/code
        "gitleaks", -- Git secrets detection
      },
    },
  },
}
