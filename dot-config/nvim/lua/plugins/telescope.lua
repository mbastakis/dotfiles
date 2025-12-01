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

    vim.keymap.set("n", "<leader>ff", function()
      builtin.find_files(themes.get_ivy())
    end, { desc = "Telescope find files" })

    vim.keymap.set("n", "<leader>fg", function()
      builtin.live_grep(themes.get_ivy())
    end, { desc = "Telescope live grep" })

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
