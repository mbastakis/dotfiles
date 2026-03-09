return {
	"akinsho/bufferline.nvim",
	version = "*",
	dependencies = { "nvim-tree/nvim-web-devicons" },
	event = "VeryLazy",
	opts = {
		options = {
			diagnostics = "nvim_lsp",
			diagnostics_indicator = function(count, level)
				local icon = level:match("error") and " " or " "
				return " " .. icon .. count
			end,
			separator_style = "thin",
			show_buffer_close_icons = false,
			show_close_icon = false,
			always_show_bufferline = false,
			indicator = { style = "none" },
			modified_icon = "●",
		},
	},
	keys = {
		{ "<S-h>", "<cmd>BufferLineCyclePrev<CR>", desc = "Buffer: Previous" },
		{ "<S-l>", "<cmd>BufferLineCycleNext<CR>", desc = "Buffer: Next" },
		{ "[b", "<cmd>BufferLineCyclePrev<CR>", desc = "Buffer: Previous" },
		{ "]b", "<cmd>BufferLineCycleNext<CR>", desc = "Buffer: Next" },
		{ "<leader>bp", "<cmd>BufferLineTogglePin<CR>", desc = "Buffer: Toggle pin" },
		{ "<leader>bP", "<cmd>BufferLineGroupClose ungrouped<CR>", desc = "Buffer: Close non-pinned" },
		{ "<leader>bo", "<cmd>BufferLineCloseOthers<CR>", desc = "Buffer: Close others" },
		{ "<leader>bl", "<cmd>BufferLineCloseRight<CR>", desc = "Buffer: Close right" },
		{ "<leader>bh", "<cmd>BufferLineCloseLeft<CR>", desc = "Buffer: Close left" },
		{ "<leader>bd", "<cmd>bdelete<CR>", desc = "Buffer: Delete current" },
	},
}
