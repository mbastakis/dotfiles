// Catppuccin Mocha color palette
// https://catppuccin.com/palette

export const colors = {
  // Base colors
  base: "#1e1e2e",
  mantle: "#181825",
  crust: "#11111b",

  // Surface colors
  surface0: "#313244",
  surface1: "#45475a",
  surface2: "#585b70",

  // Text colors
  text: "#cdd6f4",
  subtext0: "#a6adc8",
  subtext1: "#bac2de",

  // Accent colors
  green: "#a6e3a1",
  yellow: "#f9e2af",
  red: "#f38ba8",
  blue: "#89b4fa",
  mauve: "#cba6f7",
  peach: "#fab387",
  teal: "#94e2d5",
  lavender: "#b4befe",
} as const

export type Colors = typeof colors
export type ColorName = keyof Colors
