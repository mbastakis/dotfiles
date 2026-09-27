require("hlslens").setup({})

for _, key in ipairs({ "n", "N" }) do
  vim.keymap.set("n", key,
    "<Cmd>execute('normal! ' . v:count1 . '" .. key .. "')<CR><Cmd>lua require('hlslens').start()<CR>",
    { silent = true, desc = "Search " .. (key == "n" and "next" or "previous") .. " with lens" })
end

for _, key in ipairs({ "*", "#", "g*", "g#" }) do
  vim.keymap.set("n", key, key .. "<Cmd>lua require('hlslens').start()<CR>",
    { silent = true, desc = "Search word with lens" })
end
