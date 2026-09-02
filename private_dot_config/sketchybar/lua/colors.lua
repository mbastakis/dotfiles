-- Palette, read from the theme-generated colors.sh so the Nocturne Rose
-- pipeline stays the single source of truth. Values are kept as "0xaarrggbb"
-- strings: SbarLua only converts numbers for keys literally named "color".
local M = {}

local file = assert(io.open(CONFIG_DIR .. "/colors.sh", "r"), "colors.sh missing")
for line in file:lines() do
  local key, value = line:match("^([%u_]+)=(0x%x+)")
  if key then
    M[key] = value
  else
    local alias, ref = line:match('^([%u_]+)="%$([%u_]+)"')
    if alias and M[ref] then
      M[alias] = M[ref]
    end
  end
end
file:close()

M.CLEAR = "0x00000000"

-- Same hue with a different opacity (0..1).
function M.alpha(color, opacity)
  return string.format("0x%02x%s", math.floor(opacity * 255 + 0.5), color:sub(-6))
end

return M
