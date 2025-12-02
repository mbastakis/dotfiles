return {
  -- nvim-notify: Notification manager
  {
    "rcarriga/nvim-notify",
    config = function()
      require("notify").setup({
        stages = "slide", -- Animation style: fade_in_slide_out, fade, slide, static
        render = "default", -- Render style: default, minimal, simple, compact, wrapped-compact
        timeout = 3000, -- Default timeout in ms
        top_down = false, -- Notifications stack from bottom to top
        max_width = 50,
        max_height = 10,
        minimum_width = 30,
      })
      -- Set nvim-notify as the default notify handler
      vim.notify = require("notify")
    end,
  },

  -- Noice: Better UI for messages, cmdline, and popupmenu
  {
    "folke/noice.nvim",
    event = "VeryLazy",
    dependencies = {
      "MunifTanjim/nui.nvim",
      "rcarriga/nvim-notify",
    },
    config = function()
      require("noice").setup({
        lsp = {
          -- override markdown rendering so that **cmp** and other plugins use **Treesitter**
          override = {
            ["vim.lsp.util.convert_input_to_markdown_lines"] = true,
            ["vim.lsp.util.stylize_markdown"] = true,
            ["cmp.entry.get_documentation"] = true, -- requires hrsh7th/nvim-cmp
          },
          -- LSP hover and signature help with compact style
          hover = {
            enabled = true,
            silent = false,
          },
          signature = {
            enabled = true,
            auto_open = {
              enabled = true,
              trigger = true,
              throttle = 50,
            },
          },
          -- Customize documentation (hover/signature) window
          documentation = {
            view = "hover",
            opts = {
              lang = "markdown",
              replace = true,
              render = "plain",
              format = { "{message}" },
              win_options = {
                concealcursor = "n",
                conceallevel = 3,
              },
            },
          },
        },
        -- Customize views for compact borders
        views = {
          hover = {
            border = {
              style = "rounded",
              padding = { 0, 1 }, -- Reduced padding for smaller border
            },
            position = {
              row = 2,
              col = 2,
            },
            size = {
              max_width = 80,
              max_height = 20,
            },
            win_options = {
              wrap = true,
              linebreak = true,
            },
          },
        },
        -- you can enable a preset for easier configuration
        presets = {
          bottom_search = true, -- use a classic bottom cmdline for search
          command_palette = true, -- position the cmdline and popupmenu together
          long_message_to_split = true, -- long messages will be sent to a split
          inc_rename = false, -- enables an input dialog for inc-rename.nvim
          lsp_doc_border = false, -- DISABLE preset border (we customize it above)
        },
      })
    end,
  },
}
