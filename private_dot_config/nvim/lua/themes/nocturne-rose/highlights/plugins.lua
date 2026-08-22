return function(theme)
  local ui = theme.ui

  return {
    GitSignsAdd = { fg = theme.vcs.add },
    GitSignsChange = { fg = theme.vcs.change },
    GitSignsDelete = { fg = theme.vcs.delete },
    GitSignsStagedAdd = { fg = theme.vcs.add },
    GitSignsStagedChange = { fg = theme.vcs.change },
    GitSignsStagedDelete = { fg = theme.vcs.delete },
    GitSignsCurrentLineBlame = { fg = ui.muted, italic = true },
    MiniPickNormal = { fg = ui.text, bg = ui.surface },
    MiniPickBorder = { fg = ui.overlay_high, bg = ui.surface },
    MiniPickBorderText = { fg = ui.accent, bg = ui.surface, bold = true },
    MiniPickMatchCurrent = { fg = ui.text, bg = ui.overlay },
    MiniPickMatchMarked = { fg = ui.accent_secondary },
    MiniPickMatchRanges = { fg = ui.accent, bold = true },
    MiniPickPrompt = { fg = ui.accent_secondary },
    OilDir = { fg = ui.accent_secondary },
    OilDirIcon = { fg = ui.accent_secondary },
    OilFile = { fg = ui.text },
  }
end
