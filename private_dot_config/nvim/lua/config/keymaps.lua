vim.keymap.set("n", "<Esc>", "<cmd>nohlsearch<CR>", { desc = "Clear search highlights" })
vim.keymap.set("n", "<C-w>h", "<cmd>vsplit<CR>", { desc = "Split horizontal (side-by-side)" })
vim.keymap.set("n", "<C-w>v", "<cmd>split<CR>", { desc = "Split vertical (stacked)" })

vim.keymap.set("n", "-", "<cmd>Oil<CR>", { desc = "Open parent directory" })
vim.keymap.set("n", "<leader>e", "<cmd>Oil<CR>", { desc = "Open file explorer" })
vim.keymap.set("n", "<leader>uw", "<cmd>setlocal wrap!<CR>", { desc = "Toggle line wrap" })
vim.keymap.set("n", "<leader>ff", MiniPick.builtin.files, { desc = "Find files" })
vim.keymap.set("n", "<leader>fg", MiniPick.builtin.grep_live, { desc = "Find text" })

vim.cmd.packadd("nvim.undotree")
vim.keymap.set("n", "<leader>uu", "<cmd>Undotree<CR>", { desc = "Undo: Toggle tree" })
