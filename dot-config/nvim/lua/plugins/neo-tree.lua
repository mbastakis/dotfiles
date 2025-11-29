return {
  {
    "nvim-neo-tree/neo-tree.nvim",
    branch = "v3.x",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "MunifTanjim/nui.nvim",
      "nvim-tree/nvim-web-devicons",
    },
    cmd = 'Neotree', -- Lazy load on command (hidden by default)
    keys = {
      { '<leader>e', ':Neotree focus <CR>', desc = 'NeoTree toggle', silent = true },
    },
    opts = {
      close_if_last_window = true, -- Close Neo-tree if it is the last window left in the tab
      popup_border_style = 'rounded',
      enable_git_status = true,
      enable_diagnostics = true,
      default_component_configs = {
        indent = {
          indent_size = 2,
          padding = 1,
        },
      },
      window = {
        position = 'right',
        width = 30,
        mappings = {
          ['<leader>e'] = 'close_window',
          ['<space>'] = 'none', -- disable space
        },
      },
      filesystem = {
        bind_to_cwd = true,
        follow_current_file = {
          enabled = true, -- This will find and focus the file in the active buffer
        },
        hijack_netrw_behavior = 'open_current', -- netrw disabled, opening a directory opens neo-tree
        use_libuv_file_watcher = true, -- Auto refresh on file changes
        window = {
          mappings = {
            ['<leader>e'] = 'close_window',
            ['<bs>'] = 'navigate_up',
            ['.'] = 'set_root',
            ['H'] = 'toggle_hidden',
            ['/'] = 'fuzzy_finder',
            ['D'] = 'fuzzy_finder_directory',
            ['f'] = 'filter_on_submit',
            ['<c-x>'] = 'clear_filter',
          },
        },
      },
    },
  },
}

