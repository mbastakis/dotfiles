return {
  "folke/snacks.nvim",
  priority = 1000,
  lazy = false,
  opts = {
    bigfile = { enabled = true },
    quickfile = { enabled = true },
    dim = { enabled = true },
    indent = { enabled = true },
    lazygit = { enabled = true },
    git = { enabled = true },
    gitbrowse = { enabled = true },
    image = { enabled = true },
    scratch = { enabled = false },
    dashboard = {
      enabled = true,
      preset = {
        keys = {
          {
            icon = " ",
            key = "f",
            desc = "Find File",
            action = "<leader>ff",
          },
          {
            icon = " ",
            key = "g",
            desc = "Find Text",
            action = "<leader>fg",
          },
          {
            icon = " ",
            key = "e",
            desc = "Explorer",
            action = "<leader>e",
          },
          {
            icon = " ",
            key = "p",
            desc = "Explorer",
            action = "<leader>fp",
          },
          {
            icon = " ",
            key = "c",
            desc = "Config",
            action = ":lua Snacks.dashboard.pick('files', {cwd = vim.fn.stdpath('config')})",
          },
          {
            icon = "󰒲 ",
            key = "L",
            desc = "Lazy",
            action = ":Lazy",
            enabled = package.loaded.lazy ~= nil,
          },
          {
            icon = " ",
            key = "q",
            desc = "Quit",
            action = ":qa",
          },
        },
      },
      sections = {
        {
          { section = "keys", gap = 1, padding = 1 },
          { section = "startup", padding = 1 },
        },
      },
    },
  },

  keys = {
    {
      "<leader>h",
      function()
        Snacks.dashboard()
      end,
      desc = "Dashboard",
    },
    {
      "<leader>n",
      function()
        Snacks.notifier.show_history()
      end,
      desc = "Notification History",
    },
    {
      "<leader>gB",
      function()
        Snacks.gitbrowse()
      end,
      desc = "Git Browse",
    },
    {
      "<leader>gb",
      function()
        Snacks.git.blame_line()
      end,
      desc = "Git Blame Line",
    },
    {
      "<leader>gf",
      function()
        Snacks.lazygit.log_file()
      end,
      desc = "Lazygit Current File History",
    },
    {
      "<leader>gg",
      function()
        Snacks.lazygit()
      end,
      desc = "Lazygit",
    },
    {
      "<leader>gl",
      function()
        Snacks.lazygit.log()
      end,
      desc = "Lazygit Log (cwd)",
    },
    {
      "<leader>un",
      function()
        Snacks.notifier.hide()
      end,
      desc = "Dismiss All Notifications",
    },
    {
      "<c-/>",
      function()
        Snacks.terminal()
      end,
      desc = "Toggle Terminal",
      mode = { "n", "t" },
    },
  },

  init = function()
    vim.api.nvim_create_autocmd("User", {
      pattern = "VeryLazy",
      callback = function()
        -- Create autocmds for other snacks features
        Snacks.toggle.option("relativenumber", { name = "Relative Number" }):map("<leader>uL")
        Snacks.toggle.line_number():map("<leader>ul")
        Snacks.toggle
          .option("conceallevel", { off = 0, on = vim.o.conceallevel > 0 and vim.o.conceallevel or 2 })
          :map("<leader>uc")
        Snacks.toggle.treesitter():map("<leader>uT")
        Snacks.toggle.option("background", { off = "light", on = "dark", name = "Dark Background" }):map("<leader>ub")
        Snacks.toggle.inlay_hints():map("<leader>uh")
        Snacks.toggle.indent():map("<leader>ug")
        Snacks.toggle.dim():map("<leader>uD")
        Snacks.toggle
          .new({
            name = "Wrap",
            get = function()
              return vim.o.wrap
            end,
            set = function(state)
              vim.o.wrap = state
              vim.o.linebreak = state
            end,
          })
          :map("<leader>uw")
        Snacks.toggle.diagnostics():map("<leader>uv")
        Snacks.toggle
          .new({
            name = "Diagnostic Virtual Text",
            get = function()
              return vim.diagnostic.config().virtual_text ~= false
            end,
            set = function(state)
              vim.diagnostic.config({ virtual_text = state })
            end,
          })
          :map("<leader>uV")
        Snacks.toggle
          .new({
            name = "Diagnostic Underlines",
            get = function()
              return vim.diagnostic.config().underline ~= false
            end,
            set = function(state)
              vim.diagnostic.config({ underline = state })
            end,
          })
          :map("<leader>ux")
        Snacks.toggle
          .new({
            name = "Supermaven",
            get = function()
              local ok, api = pcall(require, "supermaven-nvim.api")
              return ok and api.is_running()
            end,
            set = function(state)
              if state then
                vim.cmd("SupermavenStart")
              else
                vim.cmd("SupermavenStop")
              end
            end,
          })
          :map("<leader>ua")
      end,
    })
  end,
}
