return {
  "nvim-telescope/telescope.nvim",
  tag = "v0.1.9",
  dependencies = { "nvim-lua/plenary.nvim", { "nvim-telescope/telescope-fzf-native.nvim", build = "make" } },
  config = function()
    require("telescope").setup({
      extensions = {
        fzf = {},
      },
    })

    local builtin = require("telescope.builtin")
    local themes = require("telescope.themes")

    -- Array of patterns to filter out in lowercase commands
    -- NOTE: These are Lua patterns, not globs. Special chars like . must be escaped with %
    local filter_patterns = {
      "node_modules",
      "%.git/", -- Only match .git directory, not .gitignore or other git* files
      "%.lock$",
      "package%-lock%.json",
      "yarn%.lock",
      "pnpm%-lock%.yaml",
    }

    -- Find files (filtered - excludes patterns in array)
    vim.keymap.set("n", "<leader>ff", function()
      builtin.find_files(themes.get_ivy({
        hidden = true,
        file_ignore_patterns = filter_patterns,
      }))
    end, { desc = "Telescope find files (filtered)" })

    -- Find files (show everything - no filtering)
    vim.keymap.set("n", "<leader>fF", function()
      builtin.find_files(themes.get_ivy({
        hidden = true,
        file_ignore_patterns = {},
      }))
    end, { desc = "Telescope find files (show all)" })

    -- Live grep (filtered - excludes patterns in array)
    vim.keymap.set("n", "<leader>fg", function()
      builtin.live_grep(themes.get_ivy({
        hidden = true,
        file_ignore_patterns = filter_patterns,
        additional_args = { "--hidden" },
      }))
    end, { desc = "Telescope live grep (filtered)" })

    -- Live grep (show everything - no filtering)
    vim.keymap.set("n", "<leader>fG", function()
      builtin.live_grep(themes.get_ivy({
        hidden = true,
        file_ignore_patterns = {},
        additional_args = { "--hidden" },
      }))
    end, { desc = "Telescope live grep (show all)" })

    vim.keymap.set("n", "<leader>fh", builtin.help_tags, { desc = "Telescope find help tags" })

    -- Zoxide integration - interactive directory search
    vim.keymap.set("n", "<leader>fp", function()
      local pickers = require("telescope.pickers")
      local finders = require("telescope.finders")
      local conf = require("telescope.config").values
      local actions = require("telescope.actions")
      local action_state = require("telescope.actions.state")

      pickers
        .new(
          themes.get_dropdown({
            layout_config = {
              width = 150,
            },
          }),
          {
            prompt_title = "Zoxide Projects",
            finder = finders.new_oneshot_job({ "zoxide", "query", "-l" }, {
              entry_maker = function(entry)
                return {
                  value = entry,
                  display = entry,
                  ordinal = entry,
                }
              end,
            }),
            sorter = conf.generic_sorter({}),
            attach_mappings = function(prompt_bufnr, map)
              actions.select_default:replace(function()
                actions.close(prompt_bufnr)
                local selection = action_state.get_selected_entry()
                if selection then
                  vim.cmd("cd " .. selection.value)
                  print("Changed directory to: " .. selection.value)
                end
              end)
              return true
            end,
          }
        )
        :find()
    end, { desc = "Zoxide projects" })
  end,
}
