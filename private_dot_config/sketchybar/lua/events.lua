-- Custom events. The ones with a notification name are delivered by macOS
-- itself (NSDistributedNotificationCenter), so no polling is needed.
sbar.add("event", "aerospace_workspace_change")
sbar.add("event", "aerospace_focus_change")
sbar.add("event", "bluetooth_change", "com.apple.bluetooth.status")
sbar.add("event", "input_source_change", "com.apple.Carbon.TISNotifySelectedKeyboardInputSourceChanged")
sbar.add("event", "task_change")
-- `sketchybar --trigger popup_toggle ITEM=<clock|bluetooth|tasks|flow|vpn>`
-- toggles that item's popup, e.g. from an aerospace or Karabiner binding.
sbar.add("event", "popup_toggle")
sbar.add("event", "system_stats")
sbar.add("event", "gpu_stats")
