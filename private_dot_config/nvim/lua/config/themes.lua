local M = {}

function M.setup()
  require("themes.nocturne-rose").apply()
  vim.g.active_theme = "Nocturne Rose"
end

return M
