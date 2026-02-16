return {
  "nvim-telescope/telescope.nvim",
  branch = "master",
  dependencies = { "nvim-lua/plenary.nvim", { "nvim-telescope/telescope-fzf-native.nvim", build = "make" } },
  config = function()
    require("telescope").setup({
      extensions = {
        fzf = {},
      },
    })

    -- Load the fzf extension for fuzzy sorting
    require("telescope").load_extension("fzf")

    local builtin = require("telescope.builtin")
    local themes = require("telescope.themes")
    local pickers = require("telescope.pickers")
    local finders = require("telescope.finders")
    local make_entry = require("telescope.make_entry")
    local conf = require("telescope.config").values

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

    local filter_excludes = {
      ".git",
      "node_modules",
      "*.lock",
      "package-lock.json",
      "yarn.lock",
      "pnpm-lock.yaml",
    }

    local function picker_cwd()
      local current_file = vim.api.nvim_buf_get_name(0)
      if current_file == "" then
        return vim.uv.cwd()
      end

      local root = vim.fs.root(vim.fs.dirname(current_file), { ".git" })
      return root or vim.uv.cwd()
    end

    local function find_files_live(opts)
      opts = opts or {}

      local fd_bin = nil
      if vim.fn.executable("fd") == 1 then
        fd_bin = "fd"
      elseif vim.fn.executable("fdfind") == 1 then
        fd_bin = "fdfind"
      end

      if not fd_bin then
        builtin.find_files(opts)
        return
      end

      opts.entry_maker = opts.entry_maker or make_entry.gen_from_file(opts)

      pickers
        .new(opts, {
          prompt_title = "Find Files",
          __locations_input = true,
          finder = finders.new_job(function(prompt)
            local cmd = { fd_bin, "--type", "f", "--color", "never" }

            if opts.hidden then
              table.insert(cmd, "--hidden")
            end
            if opts.no_ignore then
              table.insert(cmd, "--no-ignore")
            end
            if opts.no_ignore_parent then
              table.insert(cmd, "--no-ignore-parent")
            end
            if opts.follow then
              table.insert(cmd, "--follow")
            end

            for _, pattern in ipairs(opts.exclude or {}) do
              table.insert(cmd, "--exclude")
              table.insert(cmd, pattern)
            end

            if prompt and prompt ~= "" then
              table.insert(cmd, "--full-path")
              table.insert(cmd, "--fixed-strings")
              table.insert(cmd, prompt)
            end

            return cmd
          end, opts.entry_maker, opts.maximum_results, opts.cwd),
          previewer = false,
          sorter = conf.file_sorter(opts),
          debounce = 75,
        })
        :find()
    end

    -- Find files (filtered - excludes patterns in array)
    vim.keymap.set("n", "<leader>ff", function()
      find_files_live(themes.get_ivy({
        cwd = picker_cwd(),
        hidden = true,
        exclude = filter_excludes,
        file_ignore_patterns = filter_patterns,
      }))
    end, { desc = "Telescope find files (filtered)" })

    -- Find files (show everything - no filtering)
    vim.keymap.set("n", "<leader>fF", function()
      find_files_live(themes.get_ivy({
        cwd = picker_cwd(),
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
