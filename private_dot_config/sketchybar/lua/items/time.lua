-- Time pill: clock + agenda chip, sharing a calendar popup built from native
-- items: a month grid you can page with ‹ › (title jumps back to today) and
-- today's agenda (or the next upcoming events) from Apple Calendar.
--
-- Layout trick: the popup is horizontal, every row is a run of fixed-width
-- items, and the first item of each row carries a negative padding that
-- rewinds the cursor back to the left gutter. y_offset places the rows.
-- Every item is created once; rebuilds only re-paint them.
local colors = require("colors")
local settings = require("settings")
local h = require("helpers")

local WEEK_START = 1 -- 0 = Sunday, 1 = Monday
local EXCLUDED_CALENDARS = "Reminders"
local MAX_EVENTS = 4
local STALE_SECONDS = 900
local COCOA_EPOCH = 978307200

-- Geometry (points)
local CELL, GUT, COLS = 36, 12, 7
local W = GUT * 2 + CELL * COLS
local INNER = W - GUT * 2
local H_HEAD, H_WEEK, H_DAY, H_SEP, H_SECTION, H_EVENT = 44, 24, 32, 13, 24, 28
local MAX_WEEKS = 6
local EVENT_ROWS = MAX_EVENTS + 1 -- the extra row shows "+n more" or "nothing"

h.spacer("gap.time", settings.pill_gap)

local clock = sbar.add("item", "clock", {
  position = "right",
  icon = { drawing = false },
  label = {
    string = "--:--",
    font = settings.bold(13),
    color = colors.TEXT_COLOR,
    padding_left = 8,
    padding_right = 8,
  },
  padding_left = 0,
  padding_right = 0,
  background = { drawing = false },
  update_freq = 30,
  popup = h.merge(settings.popup, { horizontal = true, align = "right" }),
})

local agenda = sbar.add("item", "agenda", {
  position = "right",
  drawing = false,
  updates = true,
  icon = {
    string = "󰃭",
    font = settings.bold(14),
    color = colors.INFO_COLOR,
    padding_left = 8,
    padding_right = 2,
  },
  label = {
    string = "",
    font = settings.regular(13),
    color = colors.SUBTEXT_COLOR,
    max_chars = 24,
    padding_left = 2,
    padding_right = 0,
  },
  padding_left = 0,
  padding_right = 0,
  background = { drawing = false },
  update_freq = 180,
})

sbar.add("bracket", "time", { clock.name, agenda.name }, settings.bracket)

-- --- popup skeleton ----------------------------------------------------------
local POPUP = "popup." .. clock.name

local function cell(name, width, first, props)
  return sbar.add("item", name, h.merge({
    position = POPUP,
    width = width,
    padding_left = first and (GUT - W) or 0,
    padding_right = 0,
    background = { drawing = false },
    icon = { padding_left = 0, padding_right = 0 },
    label = { padding_left = 0, padding_right = 0 },
  }, props))
end

local state = {
  offset = 0,
  built_day = nil,
  built_offset = nil,
  built_at = 0,
  cell_epoch = {},
  cell_hover = {},
}

-- Header: ‹ Month Year ›
local prev = cell("cal.prev", 32, true, {
  padding_left = GUT, -- first row: no rewind
  icon = { string = "󰅁", font = settings.bold(16), color = colors.SUBTEXT_COLOR, width = 32, align = "center" },
  label = { drawing = false },
})
local title = cell("cal.title", INNER - 64, false, {
  icon = { drawing = false },
  label = { string = "", font = settings.bold(14), color = colors.TEXT_COLOR, width = INNER - 64, align = "center" },
})
local next_ = cell("cal.next", 32, false, {
  padding_right = GUT,
  icon = { string = "󰅂", font = settings.bold(16), color = colors.SUBTEXT_COLOR, width = 32, align = "center" },
  label = { drawing = false },
})
h.hover_icon(prev, colors.SUBTEXT_COLOR)
h.hover_icon(next_, colors.SUBTEXT_COLOR)

-- Weekday names
local NAMES = { "Su", "Mo", "Tu", "We", "Th", "Fr", "Sa" }
local weekdays = {}
for col = 0, COLS - 1 do
  local idx = (col + WEEK_START) % 7
  local weekend = idx == 0 or idx == 6
  weekdays[col] = cell("cal.w" .. col, CELL, col == 0, {
    padding_right = col == COLS - 1 and GUT or 0,
    icon = { drawing = false },
    label = {
      string = NAMES[idx + 1],
      font = settings.bold(11),
      color = weekend and colors.MUTED_COLOR or colors.SUBTEXT_COLOR,
      width = CELL,
      align = "center",
    },
  })
end

-- Day cells
local days = {}
for i = 0, MAX_WEEKS * COLS - 1 do
  local col = i % COLS
  local day = cell("cal.d" .. i, CELL, col == 0, {
    padding_right = col == COLS - 1 and GUT or 0,
    icon = { drawing = false },
    label = {
      string = "",
      font = settings.regular(13),
      color = colors.TEXT_COLOR,
      padding_left = 3,
      width = CELL - 6,
      align = "center",
      background = {
        drawing = true,
        color = colors.ACCENT_CHIP_OFF,
        height = 26,
        corner_radius = 7,
      },
    },
  })
  days[i] = day
  day:subscribe("mouse.clicked", function()
    local epoch = state.cell_epoch[i]
    if epoch then
      sbar.exec(string.format("open calshow:%d", epoch - COCOA_EPOCH))
    end
  end)
  day:subscribe("mouse.entered", function()
    if state.cell_hover[i] then
      sbar.animate("tanh", 8, function()
        day:set({ label = { background = { color = colors.ACCENT_CHIP_HOVER } } })
      end)
    end
  end)
  day:subscribe("mouse.exited", function()
    if state.cell_hover[i] then
      sbar.animate("tanh", 8, function()
        day:set({ label = { background = { color = colors.ACCENT_CHIP_OFF } } })
      end)
    end
  end)
end

-- Divider, section header, agenda rows
local separator = cell("cal.sep", INNER, true, {
  padding_right = GUT,
  icon = { drawing = false },
  label = { drawing = false },
  background = { drawing = true, color = colors.BORDER_COLOR, height = 1, corner_radius = 0 },
})
local section = cell("cal.section", INNER, true, {
  padding_right = GUT,
  icon = { string = "Today", font = settings.bold(11), color = colors.SUBTEXT_COLOR, width = INNER - 90, align = "left" },
  label = { string = "", font = settings.regular(11), color = colors.MUTED_COLOR, width = 90, align = "right" },
})
local events = {}
for k = 1, EVENT_ROWS do
  local row = cell("cal.e" .. k, INNER, true, {
    padding_right = GUT,
    drawing = false,
    icon = { string = "", font = settings.bold(12), color = colors.INFO_COLOR, width = 64, align = "left" },
    label = { string = "", font = settings.regular(13), color = colors.TEXT_COLOR, width = INNER - 64, align = "left", max_chars = 20 },
  })
  row:subscribe("mouse.clicked", function()
    sbar.exec("open -a Calendar")
  end)
  events[k] = row
end

-- --- data ----------------------------------------------------------------------
local ICAL = "icalBuddy -nc -nrd -eed -b '' -ps '|§|' -df '%Y-%m-%d' -tf '%H:%M' "
  .. "-iep datetime,title -po datetime,title -ec " .. h.q(EXCLUDED_CALENDARS) .. " "

local function ical(args, callback)
  h.exec(ICAL .. args .. " 2>/dev/null", function(result)
    callback(h.lines(result))
  end)
end

-- icalBuddy prints "HH:MM", "YYYY-MM-DD at HH:MM" or just "YYYY-MM-DD"
-- (all-day), and drops the date entirely for same-day listings.
local function parse_event(line)
  local dt, name = line:match("^(.-)§(.*)$")
  if not dt then
    return nil
  end
  return {
    date = dt:match("(%d%d%d%d%-%d%d%-%d%d)"),
    time = dt:match("(%d%d:%d%d)"),
    title = name,
  }
end

-- --- render --------------------------------------------------------------------
local function render(event_days, list, section_name)
  local now = os.time()
  local today = os.date("*t", now)
  local first = os.time({ year = today.year, month = today.month + state.offset, day = 1, hour = 12 })
  local ft = os.date("*t", first)
  local dim = os.date("*t", os.time({ year = ft.year, month = ft.month + 1, day = 0, hour = 12 })).day
  local prev_dim = os.date("*t", os.time({ year = ft.year, month = ft.month, day = 0, hour = 12 })).day
  local lead = ((ft.wday - 1) - WEEK_START + 7) % 7
  local weeks = (lead + dim + 6) // 7
  local same_month = ft.year == today.year and ft.month == today.month

  local count = #list
  local shown = math.min(count, MAX_EVENTS)
  local event_rows = shown
  if count > MAX_EVENTS or count == 0 then
    event_rows = event_rows + 1
  end

  local H = H_HEAD + H_WEEK + weeks * H_DAY + H_SEP + H_SECTION + event_rows * H_EVENT
  local cursor = 0
  local function row_y(height)
    local y = H // 2 - cursor - height // 2
    cursor = cursor + height
    return y
  end

  -- Header
  local y = row_y(H_HEAD)
  prev:set({ y_offset = y })
  title:set({ y_offset = y, label = { string = os.date("%B %Y", first) } })
  next_:set({ y_offset = y })

  -- Weekdays
  y = row_y(H_WEEK)
  for col = 0, COLS - 1 do
    weekdays[col]:set({ y_offset = y })
  end

  -- Day cells
  for i = 0, MAX_WEEKS * COLS - 1 do
    local col = i % COLS
    if col == 0 and i < weeks * COLS then
      y = row_y(H_DAY)
    end
    local day = days[i]
    if i >= weeks * COLS then
      day:set({ drawing = false })
      state.cell_epoch[i] = nil
      state.cell_hover[i] = false
    else
      local cell_day = i - lead + 1
      local idx = (i + WEEK_START) % 7
      local weekend = idx == 0 or idx == 6
      local label, color, font, chip, hover
      font = settings.regular(13)
      chip = colors.ACCENT_CHIP_OFF
      hover = true
      if cell_day < 1 then
        label, color = prev_dim + cell_day, colors.MUTED_COLOR
      elseif cell_day > dim then
        label, color = cell_day - dim, colors.MUTED_COLOR
      else
        label = cell_day
        color = weekend and colors.SUBTEXT_COLOR or colors.TEXT_COLOR
        if event_days[cell_day] then
          color, font = colors.INFO_COLOR, settings.bold(13)
        end
        if same_month and cell_day == today.day then
          chip, color, font, hover = colors.ACCENT_COLOR, colors.ACTIVE_TEXT_COLOR, settings.bold(13), false
        end
      end
      state.cell_epoch[i] = first + (cell_day - 1) * 86400
      state.cell_hover[i] = hover
      day:set({
        drawing = true,
        y_offset = y,
        label = { string = tostring(label), color = color, font = font, background = { color = chip } },
      })
    end
  end

  -- Divider + section header
  separator:set({ y_offset = row_y(H_SEP) })
  local summary = count == 0 and "no events" or (count == 1 and "1 event" or count .. " events")
  section:set({ y_offset = row_y(H_SECTION), icon = { string = section_name }, label = { string = summary } })

  -- Agenda rows
  local now_hm = os.date("%H:%M", now)
  local k = 0
  for index = 1, shown do
    local event = list[index]
    k = k + 1
    local when, when_color, title_color = "", colors.INFO_COLOR, colors.TEXT_COLOR
    if section_name == "Today" then
      if event.time then
        when = event.time
        if when < now_hm then
          when_color, title_color = colors.MUTED_COLOR, colors.SUBTEXT_COLOR
        end
      else
        when = "All day"
      end
    else
      when = "Soon"
      if event.date then
        local yy, mm, dd = event.date:match("(%d+)-(%d+)-(%d+)")
        when = os.date("%a %e", os.time({ year = tonumber(yy), month = tonumber(mm), day = tonumber(dd), hour = 12 })):gsub("%s+", " ")
      end
    end
    events[k]:set({
      drawing = true,
      y_offset = row_y(H_EVENT),
      icon = { string = when, color = when_color },
      label = { string = event.title, color = title_color },
    })
  end
  if count == 0 then
    k = k + 1
    events[k]:set({
      drawing = true,
      y_offset = row_y(H_EVENT),
      icon = { string = "" },
      label = { string = "Nothing scheduled", color = colors.MUTED_COLOR },
    })
  elseif count > MAX_EVENTS then
    k = k + 1
    events[k]:set({
      drawing = true,
      y_offset = row_y(H_EVENT),
      icon = { string = "" },
      label = { string = "+" .. (count - MAX_EVENTS) .. " more in Calendar", color = colors.MUTED_COLOR },
    })
  end
  for index = k + 1, EVENT_ROWS do
    events[index]:set({ drawing = false })
  end

  clock:set({ popup = { height = H } })
  state.built_day = today.day
  state.built_offset = state.offset
  state.built_at = now
end

local function build(callback)
  local today = os.date("*t")
  local first = os.time({ year = today.year, month = today.month + state.offset, day = 1, hour = 12 })
  local ft = os.date("*t", first)
  local dim = os.date("*t", os.time({ year = ft.year, month = ft.month + 1, day = 0, hour = 12 })).day
  local ym = os.date("%Y-%m", first)
  local today_str = os.date("%Y-%m-%d")

  ical(string.format("eventsFrom:%s-01 to:%s-%02d", ym, ym, dim), function(month_lines)
    local event_days = {}
    for _, line in ipairs(month_lines) do
      local event = parse_event(line)
      if event and event.date and event.date:sub(1, 7) == ym then
        event_days[tonumber(event.date:sub(9, 10))] = true
      end
    end
    ical("eventsToday", function(today_lines)
      local list = {}
      for _, line in ipairs(today_lines) do
        local event = parse_event(line)
        if event then
          list[#list + 1] = event
        end
      end
      if #list > 0 then
        render(event_days, list, "Today")
        if callback then
          callback()
        end
        return
      end
      ical("eventsToday+14", function(upcoming_lines)
        for _, line in ipairs(upcoming_lines) do
          local event = parse_event(line)
          if event and event.date ~= today_str then
            list[#list + 1] = event
          end
        end
        render(event_days, list, "Upcoming")
        if callback then
          callback()
        end
      end)
    end)
  end)
end

local function stale()
  return state.built_day ~= os.date("*t").day
    or state.built_offset ~= state.offset
    or os.time() - state.built_at > STALE_SECONDS
end

local popup
local open_popup
popup = h.popup(clock, {
  on_close = function()
    -- Always reopen on the current month.
    state.offset = 0
  end,
  toggle = function()
    open_popup()
  end,
})

-- Open immediately when fresh; otherwise build first so the popup never
-- shows a stale month.
open_popup = function()
  if popup.open then
    popup.hide()
  elseif stale() then
    build(function()
      popup.show()
    end)
  else
    popup.show()
  end
end

local function navigate(step)
  if step == 0 then
    state.offset = 0
  else
    state.offset = state.offset + step
  end
  build()
end

prev:subscribe("mouse.clicked", function() navigate(-1) end)
next_:subscribe("mouse.clicked", function() navigate(1) end)
title:subscribe("mouse.clicked", function() navigate(0) end)

clock:subscribe("mouse.clicked", open_popup)
agenda:subscribe("mouse.clicked", open_popup)
agenda:subscribe("mouse.exited.global", function()
  if popup.open then
    popup.hide()
  end
end)

clock:subscribe({ "routine", "forced", "system_woke" }, function()
  clock:set({ label = { string = os.date("%H:%M") } })
end)

-- Bar chip: next upcoming event of the day.
local function update_agenda()
  h.exec("icalBuddy -n -nc -nrd -eed -b '' -ps '|§|' -df '' -tf '%H:%M' -iep datetime,title -po datetime,title -ec "
    .. h.q(EXCLUDED_CALENDARS) .. " eventsToday 2>/dev/null | head -n1", function(line)
    local event = parse_event(line)
    if not event then
      agenda:set({ drawing = false })
      return
    end
    local label = event.time and (event.time .. " " .. event.title) or event.title
    agenda:set({ drawing = true, label = { string = label } })
  end)
end

agenda:subscribe({ "routine", "forced", "system_woke" }, update_agenda)
