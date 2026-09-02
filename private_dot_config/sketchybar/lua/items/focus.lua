-- Focus pill: Taskwarrior ready count + Flow pomodoro timer.
local colors = require("colors")
local settings = require("settings")
local h = require("helpers")

h.spacer("gap.focus", settings.pill_gap)

-- --- flow ------------------------------------------------------------------------------
-- Hidden until Flow is installed; a dim timer icon when it is not running
-- (click launches it); the remaining time in the phase color while a session
-- runs. The popup offers start / pause / skip / reset / show.
local FLOW_APP = "/Applications/Flow.app"

local flow = sbar.add("item", "flow", {
  position = "right",
  drawing = false,
  updates = true,
  icon = { string = "󰔛", color = colors.MUTED_COLOR, padding_left = 6, padding_right = 4 },
  label = { drawing = false, font = settings.bold(13), padding_left = 0, padding_right = 8 },
  padding_left = 0,
  padding_right = 0,
  background = { drawing = false },
  update_freq = 15,
  popup = h.merge(settings.popup, { horizontal = true, align = "center" }),
})
local flow_popup = h.popup(flow)
local flow_running = false

local function update_flow()
  h.exec("[ -d " .. h.q(FLOW_APP) .. " ] && (pgrep -xq Flow && echo running || echo idle)", function(state)
    if state == "" then
      flow:set({ drawing = false })
      flow_running = false
      return
    end
    if state ~= "running" then
      flow_running = false
      flow:set({ drawing = true, update_freq = 15, icon = { color = colors.MUTED_COLOR }, label = { drawing = false } })
      return
    end
    flow_running = true
    h.exec("osascript -e 'tell application \"Flow\" to return (getTime as text) & \"|\" & (getPhase as text)' 2>/dev/null", function(result)
      local time, phase = result:match("^(.-)|(.*)$")
      local color = colors.SUBTEXT_COLOR
      if phase == "Flow" then
        color = colors.SUCCESS_COLOR
      elseif phase == "Break" then
        color = colors.INFO_COLOR
      end
      flow:set({
        drawing = true,
        update_freq = 1,
        icon = { color = color },
        label = { drawing = true, string = time or "--:--", color = color },
      })
    end)
  end)
end

flow:subscribe({ "routine", "forced", "system_woke" }, update_flow)
flow:subscribe("mouse.clicked", function()
  if flow_running then
    flow_popup.toggle()
  else
    sbar.exec("open -a Flow")
    sbar.delay(2, update_flow)
  end
end)
h.hover_icon(flow, function()
  return flow_running and nil or colors.MUTED_COLOR
end)

local FLOW_BUTTONS = {
  { name = "start", glyph = "󰐊", action = "start" },
  { name = "pause", glyph = "󰏤", action = "stop" },
  { name = "skip", glyph = "󰒭", action = "skip" },
  { name = "reset", glyph = "󰑙", action = "reset" },
  { name = "show", glyph = "󰖯", action = "show" },
}
for _, entry in ipairs(FLOW_BUTTONS) do
  local button = sbar.add("item", "flow." .. entry.name, h.merge(settings.icon_button(entry.glyph), {
    position = "popup." .. flow.name,
    width = 32,
    icon = { width = 32 },
    padding_left = 2,
    padding_right = 2,
  }))
  h.hover_icon(button, colors.MUTED_COLOR)
  button:subscribe("mouse.clicked", function()
    flow_popup.hide()
    h.exec("osascript -e 'tell application \"Flow\" to " .. entry.action .. "' >/dev/null 2>&1", update_flow)
  end)
end

-- --- taskwarrior ------------------------------------------------------------------------
-- The bar shows how many tasks are Ready (+next); the icon turns amber when
-- something is due today and red when something is overdue. The popup lists
-- the most urgent Ready tasks: left click starts/stops, right click completes.
-- Updates are event driven: a Taskwarrior on-exit hook triggers task_change.
local TASK = "/opt/homebrew/bin/task rc.verbose=nothing rc.confirmation=off rc.hooks=off rc.gc=off"
local MAX_ROWS = 8
local BOARD_URL = "https://taskboard.mbastakis.com"
local SYNC = os.getenv("HOME") .. "/bin/task-sync"

local tasks = sbar.add("item", "tasks", {
  position = "right",
  updates = true,
  icon = { string = "󰝖", color = colors.MUTED_COLOR, padding_left = 8, padding_right = 4 },
  label = {
    string = "--",
    font = settings.bold(13),
    color = colors.SUBTEXT_COLOR,
    padding_left = 0,
    padding_right = 6,
  },
  padding_left = 0,
  padding_right = 0,
  background = { drawing = false },
  update_freq = 600,
  popup = h.merge(settings.popup, { align = "center" }),
})
local tasks_toggle
local tasks_popup = h.popup(tasks, {
  toggle = function()
    tasks_toggle()
  end,
})
local task_rows = h.row_pool("tw", "popup." .. tasks.name, h.merge(settings.popup_row, {
  padding_left = 8,
  padding_right = 8,
  icon = { font = settings.bold(12), width = 58, align = "left", padding_left = 4, padding_right = 4 },
  label = { max_chars = 40, padding_left = 0, padding_right = 8 },
}))

local counts = { ready = 0, overdue = 0, due_today = 0 }
local task_label_color = colors.SUBTEXT_COLOR

-- Overdue means the due *day* has passed; a task due today stays amber all
-- day (Taskwarrior's +OVERDUE would flip it red at midnight).
local function update_counts(callback)
  h.exec(TASK .. " status:pending +next count; " .. TASK .. " status:pending due.before:today count; "
    .. TASK .. " status:pending due:today count", function(result)
    local lines = h.lines(result)
    counts.ready = tonumber(lines[1]) or 0
    counts.overdue = tonumber(lines[2]) or 0
    counts.due_today = tonumber(lines[3]) or 0
    local color = colors.MUTED_COLOR
    task_label_color = colors.SUBTEXT_COLOR
    if counts.due_today > 0 then
      color = colors.WARNING_COLOR
    end
    if counts.overdue > 0 then
      color, task_label_color = colors.ERROR_COLOR, colors.TEXT_COLOR
    end
    sbar.animate("tanh", 8, function()
      tasks:set({ icon = { color = color }, label = { string = tostring(counts.ready), color = task_label_color } })
    end)
    if callback then
      callback()
    end
  end)
end

-- Taskwarrior stores dates as UTC "YYYYMMDDTHHMMSSZ".
local function parse_utc(stamp)
  local y, m, d, hh, mm, ss = tostring(stamp or ""):match("^(%d%d%d%d)(%d%d)(%d%d)T(%d%d)(%d%d)(%d%d)Z$")
  if not y then
    return nil
  end
  local utc = os.time({ year = tonumber(y), month = tonumber(m), day = tonumber(d), hour = tonumber(hh), min = tonumber(mm), sec = tonumber(ss) })
  -- os.time interprets the table as local time; correct by the local offset.
  local offset = os.time(os.date("*t", utc)) - os.time(os.date("!*t", utc))
  return utc + offset
end

-- Relative, compact due label: overdue dates, today / tmrw, weekday within a
-- week, otherwise "Mon d".
local function due_label(due)
  local epoch = parse_utc(due)
  if not epoch then
    return nil, nil
  end
  local today = os.date("*t")
  local midnight = os.time({ year = today.year, month = today.month, day = today.day, hour = 0 })
  local days = (epoch - midnight) // 86400
  local text
  if days < 0 then
    text = os.date("%b %e", epoch):gsub("%s+", " ")
    return text, colors.ERROR_COLOR
  elseif days == 0 then
    return "today", colors.WARNING_COLOR
  elseif days == 1 then
    text = "tmrw"
  elseif days < 7 then
    text = os.date("%a", epoch)
  else
    text = os.date("%b %e", epoch):gsub("%s+", " ")
  end
  return text, colors.SUBTEXT_COLOR
end

local build_task_popup

local function task_action(uuid, action)
  h.exec(TASK .. " " .. h.q(uuid) .. " " .. action .. " >/dev/null 2>&1", function()
    build_task_popup()
    update_counts()
  end)
end

local function footer(label, glyph, on_click)
  task_rows.next({
    icon = { string = glyph, color = colors.MUTED_COLOR, font = settings.bold(14), width = 26, align = "center" },
    label = { string = label, color = colors.SUBTEXT_COLOR, font = settings.regular(12) },
  }, { hover = true, on_click = on_click })
end

build_task_popup = function(callback)
  h.exec_json(TASK .. " rc.json.array=on status:pending +next export 2>/dev/null", function(list)
    list = list or {}
    table.sort(list, function(a, b)
      return (a.urgency or 0) > (b.urgency or 0)
    end)
    task_rows.begin()

    local detail, detail_color = "", colors.WARNING_COLOR
    if counts.overdue > 0 then
      detail, detail_color = counts.overdue .. " overdue", colors.ERROR_COLOR
    elseif counts.due_today > 0 then
      detail = counts.due_today .. " due today"
    end
    task_rows.next(h.merge(settings.popup_header, {
      icon = { drawing = true, string = counts.ready .. " ready", font = settings.bold(11), color = colors.SUBTEXT_COLOR, width = "dynamic", align = "left", padding_left = 4, padding_right = 8 },
      label = { string = detail, color = detail_color, drawing = detail ~= "", padding_left = 0, padding_right = 4 },
    }))

    for index, task in ipairs(list) do
      if index > MAX_ROWS then
        break
      end
      local when, when_color = due_label(task.due)
      if not when then
        when, when_color = "—", colors.MUTED_COLOR
      end
      local description = task.description or ""
      local label_color = colors.TEXT_COLOR
      if task.start then
        description = "󰐊 " .. description
        label_color = colors.SUCCESS_COLOR
      end
      if task.project and task.project ~= "" then
        description = description .. "  ·  " .. task.project
      end
      local uuid, active = task.uuid, task.start ~= nil
      task_rows.next({
        icon = { string = when, color = when_color },
        label = { string = description, color = label_color },
      }, {
        hover = true,
        on_click = function(env)
          if env.BUTTON == "right" then
            task_action(uuid, "done")
          else
            task_action(uuid, active and "stop" or "start")
          end
        end,
      })
    end

    if #list == 0 then
      task_rows.next({
        icon = { string = "" },
        label = { string = "Nothing ready", color = colors.MUTED_COLOR },
      })
    elseif #list > MAX_ROWS then
      task_rows.next({
        icon = { string = "" },
        label = { string = "+" .. (#list - MAX_ROWS) .. " more", color = colors.MUTED_COLOR, font = settings.regular(12) },
      })
    end

    footer("Open board", "󰕮", function()
      tasks_popup.hide()
      sbar.exec("open " .. h.q(BOARD_URL))
    end)
    footer("Sync now", "󰓦", function()
      tasks_popup.hide()
      h.exec(h.q(SYNC) .. " --quiet >/dev/null 2>&1; " .. TASK .. " status:pending count >/dev/null", function()
        update_counts()
      end)
    end)
    task_rows.finish()
    if callback then
      callback()
    end
  end)
end

tasks:subscribe({ "task_change", "routine", "forced", "system_woke" }, function()
  update_counts(function()
    if tasks_popup.open then
      build_task_popup()
    end
  end)
end)
tasks_toggle = function()
  if tasks_popup.open then
    tasks_popup.hide()
  else
    update_counts(function()
      build_task_popup(tasks_popup.show)
    end)
  end
end
tasks:subscribe("mouse.clicked", tasks_toggle)
tasks:subscribe("mouse.entered", function()
  sbar.animate("tanh", 8, function()
    tasks:set({ label = { color = colors.TEXT_COLOR } })
  end)
end)
tasks:subscribe("mouse.exited", function()
  sbar.animate("tanh", 8, function()
    tasks:set({ label = { color = task_label_color } })
  end)
end)

sbar.add("bracket", "focus", { tasks.name, flow.name }, settings.bracket)
