return {
  "olimorris/codecompanion.nvim",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "nvim-treesitter/nvim-treesitter",
  },
  config = function()
    require("codecompanion").setup({
      -- Configure adapters (ACP adapters like OpenCode)
      adapters = {
        acp = {
          opts = {
            show_presets = false, -- Only show configured adapters
          },
          -- Extend OpenCode adapter with model choices
          opencode = function()
            return require("codecompanion.adapters").extend("opencode", {
              schema = {
                model = {
                  default = "amazon-bedrock/anthropic.claude-opus-4-5-20251101-v1:0",
                  choices = {
                    -- Primary model (Bedrock)
                    "amazon-bedrock/anthropic.claude-opus-4-5-20251101-v1:0",
                    -- OpenCode free models
                    "opencode/trinity-large-preview-free",
                    "opencode/minimax-m2.1-free",
                    "opencode/kimi-k2.5-free",
                    "opencode/glm-4.7-free",
                    "opencode/big-pickle",
                    -- OpenAI
                    "openai/gpt-5.2-codex",
                    "openai/gpt-5.1-codex-max",
                  },
                },
              },
            })
          end,
        },
      },

      -- Use 'interactions' (strategies is deprecated)
      interactions = {
        chat = {
          adapter = "opencode",
          slash_commands = {
            opts = {
              provider = "snacks",
            },
            -- Override individual slash command providers
            ["buffer"] = {
              opts = {
                provider = "snacks",
              },
            },
            ["file"] = {
              opts = {
                provider = "snacks",
              },
            },
            ["symbols"] = {
              opts = {
                provider = "snacks",
              },
            },
            ["fetch"] = {
              opts = {
                provider = "snacks",
              },
            },
            ["help"] = {
              opts = {
                provider = "snacks",
              },
            },
          },
          opts = {
            completion_provider = "blink",
          },
        },
      },

      -- Display configuration
      display = {
        action_palette = {
          provider = "snacks",
        },
        chat = {
          window = {
            layout = "vertical",
            width = 0.4,
          },
          show_token_count = true,
        },
      },

      ignore_warnings = true,
    })

    -- Keymaps
    vim.keymap.set({ "n", "v" }, "<leader>ap", "<cmd>CodeCompanionActions<cr>", { desc = "CodeCompanion Actions" })
    vim.keymap.set({ "n", "v" }, "<leader>ac", "<cmd>CodeCompanionChat Toggle<cr>", { desc = "Toggle AI Chat" })
  end,
}
