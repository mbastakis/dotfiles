local M = {}

local function merge(groups, additions)
  for name, highlight in pairs(additions) do
    groups[name] = highlight
  end
end

function M.apply()
  vim.cmd.highlight("clear")
  if vim.fn.exists("syntax_on") == 1 then
    vim.cmd.syntax("reset")
  end

  vim.g.colors_name = "nocturne-rose"
  vim.o.background = "dark"

  local theme = require("themes.nocturne-rose.theme")
  local groups = {}

  merge(groups, require("themes.nocturne-rose.highlights.editor")(theme))
  merge(groups, require("themes.nocturne-rose.highlights.syntax")(theme))
  merge(groups, require("themes.nocturne-rose.highlights.plugins")(theme))

  for group, highlight in pairs(groups) do
    vim.api.nvim_set_hl(0, group, highlight)
  end

  for index, color in ipairs(theme.terminal) do
    vim.g["terminal_color_" .. (index - 1)] = color
  end
end

return M
