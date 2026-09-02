-- Connectivity pill: Bluetooth + VPN.
local colors = require("colors")
local settings = require("settings")
local h = require("helpers")

h.spacer("gap.connectivity", settings.pill_gap)

-- --- bluetooth ------------------------------------------------------------------------
-- Bar icon reflects power / connection / headphones state; the popup lists
-- connected devices with battery, paired devices you can click to connect,
-- and a power toggle. State comes from system_profiler (fast, JSON);
-- blueutil only performs actions because it is slow.
local ICON_BT, ICON_BT_CONNECTED, ICON_BT_OFF, ICON_HEADPHONES = "󰂯", "󰂱", "󰂲", "󰋋"
local DEVICE_ICONS = {
  Keyboard = "󰌌",
  Mouse = "󰍽",
  Trackpad = "󰍽",
  Headphones = ICON_HEADPHONES,
  Headset = ICON_HEADPHONES,
  Speaker = "󰓃",
  Watch = "󰖉",
  Phone = "󰄜",
  Smartphone = "󰄜",
  Cellphone = "󰄜",
  Gamepad = "󰊗",
  ["Game Controller"] = "󰊗",
}
local MAX_PAIRED = 6

local bluetooth = sbar.add("item", "bluetooth", h.merge(settings.icon_button(ICON_BT), {
  position = "right",
  updates = true,
  update_freq = 60,
  popup = h.merge(settings.popup, { align = "center" }),
}))

local bt_resting = colors.MUTED_COLOR
local bt_rows = h.row_pool("bt", "popup." .. bluetooth.name, settings.popup_row)

local function battery_color(level)
  local number = tonumber((tostring(level or "")):match("(%d+)"))
  if not number then
    return colors.SUBTEXT_COLOR
  elseif number <= 20 then
    return colors.ERROR_COLOR
  elseif number <= 50 then
    return colors.WARNING_COLOR
  end
  return colors.SUCCESS_COLOR
end

-- system_profiler lists devices as [{ ["Name"] = {props} }, ...].
local function devices(list)
  local out = {}
  for _, entry in ipairs(list or {}) do
    for name, props in pairs(entry) do
      out[#out + 1] = {
        name = name,
        minor = props.device_minorType or "",
        battery = props.device_batteryLevelMain or props.device_batteryLevelLeft,
        address = props.device_address,
      }
    end
  end
  table.sort(out, function(a, b)
    return a.name < b.name
  end)
  return out
end

local function snapshot(callback)
  h.exec_json("system_profiler SPBluetoothDataType -json -detailLevel basic 2>/dev/null", function(data)
    local bt = data and data.SPBluetoothDataType and data.SPBluetoothDataType[1] or {}
    local controller = bt.controller_properties or {}
    callback({
      power = controller.controller_state == "attrib_on",
      connected = devices(bt.device_connected),
      paired = devices(bt.device_not_connected),
    })
  end)
end

local function update_icon(state)
  local icon, color = ICON_BT, colors.MUTED_COLOR
  if not state.power then
    icon = ICON_BT_OFF
  else
    local headphones = false
    for _, device in ipairs(state.connected) do
      if device.minor == "Headphones" or device.minor == "Headset" then
        headphones = true
      end
    end
    if headphones then
      icon, color = ICON_HEADPHONES, colors.SUBTEXT_COLOR
    elseif #state.connected > 0 then
      icon = ICON_BT_CONNECTED
    end
  end
  bt_resting = color
  sbar.animate("tanh", 8, function()
    bluetooth:set({ icon = { string = icon, color = color } })
  end)
end

local bt_popup
local bt_toggle
bt_popup = h.popup(bluetooth, {
  toggle = function()
    bt_toggle()
  end,
})

local function bt_action(command)
  bt_popup.hide()
  sbar.exec("(" .. command .. " >/dev/null 2>&1; sketchybar --trigger bluetooth_change) &")
end

local function build_popup(state)
  bt_rows.begin()
  if state.power then
    bt_rows.next(h.merge(settings.popup_header, { label = { string = "Connected" } }))
    if #state.connected == 0 then
      bt_rows.next({
        icon = { string = ICON_BT, color = colors.MUTED_COLOR },
        label = { string = "No devices connected", color = colors.MUTED_COLOR },
      })
    end
    local seen = {}
    for _, device in ipairs(state.connected) do
      seen[device.name] = true
      local suffix = device.battery and (" · " .. device.battery) or ""
      bt_rows.next({
        icon = { string = DEVICE_ICONS[device.minor] or ICON_BT, color = battery_color(device.battery) },
        label = { string = device.name .. suffix, color = colors.TEXT_COLOR },
      })
    end
    local shown = 0
    for _, device in ipairs(state.paired) do
      if device.address and not seen[device.name] and shown < MAX_PAIRED then
        seen[device.name] = true
        shown = shown + 1
        if shown == 1 then
          bt_rows.next(h.merge(settings.popup_header, { label = { string = "Paired" } }))
        end
        local address = device.address
        bt_rows.next({
          icon = { string = DEVICE_ICONS[device.minor] or ICON_BT, color = colors.MUTED_COLOR },
          label = { string = device.name, color = colors.SUBTEXT_COLOR },
        }, {
          hover = true,
          on_click = function()
            bt_action("blueutil --connect " .. h.q(address))
          end,
        })
      end
    end
  end
  bt_rows.next({
    icon = { string = state.power and ICON_BT_OFF or ICON_BT, color = colors.SUBTEXT_COLOR },
    label = { string = state.power and "Turn Bluetooth off" or "Turn Bluetooth on", color = colors.SUBTEXT_COLOR },
  }, {
    hover = true,
    on_click = function()
      bt_action("blueutil -p " .. (state.power and "0" or "1"))
    end,
  })
  bt_rows.finish()
end

-- Header rows must not draw a hover chip; reset their background each time.
local function refresh(with_popup, callback)
  snapshot(function(state)
    update_icon(state)
    if with_popup then
      build_popup(state)
    end
    if callback then
      callback()
    end
  end)
end

bluetooth:subscribe({ "bluetooth_change", "system_woke", "routine", "forced" }, function()
  refresh(bt_popup.open)
end)
bt_toggle = function()
  if bt_popup.open then
    bt_popup.hide()
  else
    refresh(true, bt_popup.show)
  end
end
bluetooth:subscribe("mouse.clicked", bt_toggle)
h.hover_icon(bluetooth, function()
  return bt_resting
end)

-- --- vpn ----------------------------------------------------------------------------------
local vpn = sbar.add("item", "vpn", h.merge(settings.icon_button("󰦝"), {
  position = "right",
  popup = h.merge(settings.popup, { horizontal = true, align = "center" }),
}))
local vpn_popup = h.popup(vpn)
vpn:subscribe("mouse.clicked", vpn_popup.toggle)
h.hover_icon(vpn, colors.MUTED_COLOR)

local VPN_APPS = {
  { name = "tailscale", image = "app.io.tailscale.ipn.macos", app = "Tailscale" },
  { name = "harmony", image = "app.com.safervpn.osx.smb", app = "Harmony SASE" },
  { name = "wireguard", image = "app.com.wireguard.macos", app = "WireGuard" },
}
for _, entry in ipairs(VPN_APPS) do
  local button = sbar.add("item", "vpn." .. entry.name, {
    position = "popup." .. vpn.name,
    background = {
      drawing = true,
      color = colors.CLEAR,
      image = { string = entry.image, scale = 0.65, padding_left = 8, padding_right = 8 },
    },
  })
  button:subscribe("mouse.clicked", function()
    vpn_popup.hide()
    sbar.exec(h.q(PLUGIN_DIR .. "/vpn_menu.sh") .. " " .. h.q(entry.app))
  end)
end

sbar.add("bracket", "connectivity", { bluetooth.name, vpn.name }, settings.bracket)
