local colors = require("colors")

local M = {}

function M.trim(s)
  return (tostring(s or ""):gsub("^%s+", ""):gsub("%s+$", ""))
end

-- Single-quote a string for sh.
function M.q(s)
  return "'" .. tostring(s):gsub("'", "'\\''") .. "'"
end

function M.lines(s)
  local out = {}
  for line in tostring(s or ""):gmatch("[^\n]+") do
    out[#out + 1] = line
  end
  return out
end

function M.split(s, sep)
  local out = {}
  local pattern = "([^" .. sep .. "]*)" .. sep .. "?"
  for piece in tostring(s):gmatch(pattern) do
    out[#out + 1] = piece
  end
  if out[#out] == "" then
    out[#out] = nil
  end
  return out
end

-- Deep merge of property tables; later arguments win.
function M.merge(...)
  local result = {}
  for _, source in ipairs({ ... }) do
    for key, value in pairs(source or {}) do
      if type(value) == "table" and type(result[key]) == "table" then
        result[key] = M.merge(result[key], value)
      elseif type(value) == "table" then
        result[key] = M.merge({}, value)
      else
        result[key] = value
      end
    end
  end
  return result
end

-- Run a shell command and hand the (trimmed) string result to the callback.
-- sbar.exec parses JSON automatically; use M.exec_json for that.
function M.exec(command, callback)
  sbar.exec(command, function(result, exit_code)
    if callback then
      if type(result) ~= "string" then
        result = ""
      end
      callback(M.trim(result), exit_code)
    end
  end)
end

function M.exec_json(command, callback)
  sbar.exec(command, function(result, exit_code)
    if type(result) ~= "table" then
      result = nil
    end
    callback(result, exit_code)
  end)
end

-- Hover affordance for icon-only toggles: brighten under the pointer and
-- settle back to the resting color (a value or a function) on exit.
function M.hover_icon(item, resting)
  item:subscribe("mouse.entered", function()
    sbar.animate("tanh", 8, function()
      item:set({ icon = { color = colors.TEXT_COLOR } })
    end)
  end)
  item:subscribe("mouse.exited", function()
    local color = type(resting) == "function" and resting() or resting or colors.MUTED_COLOR
    sbar.animate("tanh", 8, function()
      item:set({ icon = { color = color } })
    end)
  end)
end

-- Hover affordance for clickable rows: a faint accent chip fades in and out.
-- The row keeps background.drawing on with a transparent color so the fade
-- animates instead of snapping.
function M.hover_row(item, enabled)
  item:subscribe("mouse.entered", function()
    if enabled and not enabled() then
      return
    end
    sbar.animate("tanh", 8, function()
      item:set({ background = { color = colors.ACCENT_CHIP_HOVER } })
    end)
  end)
  item:subscribe("mouse.exited", function()
    if enabled and not enabled() then
      return
    end
    sbar.animate("tanh", 8, function()
      item:set({ background = { color = colors.ACCENT_CHIP_OFF } })
    end)
  end)
end

-- Popup controller: click toggles, leaving the item and its popup closes.
-- opts.on_open runs before the popup shows (rebuild rows); opts.on_close
-- after it hides.
function M.popup(item, opts)
  opts = opts or {}
  local ctl = { open = false }

  function ctl.show()
    if opts.on_open then
      opts.on_open()
    end
    item:set({ popup = { drawing = true } })
    ctl.open = true
  end

  function ctl.hide()
    item:set({ popup = { drawing = false } })
    ctl.open = false
    if opts.on_close then
      opts.on_close()
    end
  end

  function ctl.toggle()
    if ctl.open then
      ctl.hide()
    else
      ctl.show()
    end
  end

  -- Some hosts redraw their popup after a rebuild; cycling forces a layout.
  function ctl.refresh()
    if ctl.open then
      item:set({ popup = { drawing = false } })
      item:set({ popup = { drawing = true } })
    end
  end

  item:subscribe("mouse.exited.global", function()
    if ctl.open then
      ctl.hide()
    end
  end)

  -- Programmatic toggle: `sketchybar --trigger popup_toggle ITEM=<name>`.
  item:subscribe("popup_toggle", function(env)
    if env.ITEM == item.name then
      if opts.toggle then
        opts.toggle()
      else
        ctl.toggle()
      end
    end
  end)

  return ctl
end

-- Invisible fixed-width gap between two pills.
function M.spacer(name, width)
  return sbar.add("item", name, {
    position = "right",
    width = width,
    padding_left = 0,
    padding_right = 0,
    icon = { drawing = false },
    label = { drawing = false },
    background = { drawing = false },
  })
end

-- Pool of reusable popup rows. Rows are created once (in order) and
-- re-painted on every rebuild; unused ones are hidden. Each row can carry an
-- on_click handler and a hover chip for the current rebuild only.
function M.row_pool(prefix, position, defaults)
  local rows, meta = {}, {}
  local pool = { count = 0 }

  local function ensure(index)
    if rows[index] then
      return rows[index]
    end
    local row = sbar.add("item", prefix .. "." .. index, M.merge(defaults, { position = position, drawing = false }))
    meta[index] = {}
    row:subscribe("mouse.clicked", function(env)
      local handler = meta[index].on_click
      if handler then
        handler(env)
      end
    end)
    M.hover_row(row, function()
      return meta[index].hover
    end)
    rows[index] = row
    return row
  end

  function pool.begin()
    pool.count = 0
  end

  -- props: item properties; opts.on_click(env), opts.hover (bool)
  function pool.next(props, opts)
    pool.count = pool.count + 1
    local row = ensure(pool.count)
    opts = opts or {}
    meta[pool.count].on_click = opts.on_click
    meta[pool.count].hover = opts.hover or false
    row:set(M.merge({ drawing = true, background = { color = colors.ACCENT_CHIP_OFF } }, props))
    return row
  end

  function pool.finish()
    for index = pool.count + 1, #rows do
      rows[index]:set({ drawing = false })
      meta[index].on_click = nil
      meta[index].hover = false
    end
  end

  return pool
end

-- Strip emoji and pictographs: the bar's iconography is monochrome Nerd Font
-- glyphs, and a color emoji becomes an accidental focal point.
function M.strip_emoji(text)
  local ok, out = pcall(function()
    local pieces = {}
    for _, cp in utf8.codes(text) do
      local emoji = (cp >= 0x1F000 and cp <= 0x1FAFF)
        or (cp >= 0x2600 and cp <= 0x27BF)
        or (cp >= 0x2B00 and cp <= 0x2BFF)
        or (cp >= 0xFE00 and cp <= 0xFE0F)
        or cp == 0x200D
      if not emoji then
        pieces[#pieces + 1] = utf8.char(cp)
      end
    end
    return table.concat(pieces)
  end)
  if not ok then
    return text
  end
  out = out:gsub("%s%s+", " ")
  out = M.trim(out):gsub("%s*[·—%-]%s*$", "")
  return out
end

return M
