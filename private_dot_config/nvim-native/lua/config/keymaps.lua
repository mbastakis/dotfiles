vim.keymap.set("n", "-", "<cmd>Oil<cr>", { desc = "Open parent directory" })
vim.keymap.set("n", "<leader>ff", MiniPick.builtin.files, { desc = "Find files" })
vim.keymap.set("n", "<leader>fg", MiniPick.builtin.grep_live, { desc = "Find text" })
