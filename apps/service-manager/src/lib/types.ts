// Service types for the service-manager TUI

export type ServiceStatus = "running" | "stopped" | "not_installed"

export interface Service {
  label: string
  plistPath: string // Source path in dotfiles
  installedPath: string // Path in ~/Library/LaunchAgents/
  status: ServiceStatus
  pid?: number
  exitCode?: number
  program: string[]
  runAtLoad: boolean
  keepAlive: boolean
  stdoutPath?: string
  stderrPath?: string
  workingDirectory?: string
  environmentVariables?: Record<string, string>
}

export interface PlistData {
  Label: string
  ProgramArguments?: string[]
  RunAtLoad?: boolean
  KeepAlive?: boolean
  StandardOutPath?: string
  StandardErrorPath?: string
  WorkingDirectory?: string
  EnvironmentVariables?: Record<string, string>
}

// Catppuccin Mocha colors
export const colors = {
  base: "#1e1e2e",
  mantle: "#181825",
  crust: "#11111b",
  surface0: "#313244",
  surface1: "#45475a",
  surface2: "#585b70",
  text: "#cdd6f4",
  subtext0: "#a6adc8",
  subtext1: "#bac2de",
  green: "#a6e3a1",
  yellow: "#f9e2af",
  red: "#f38ba8",
  blue: "#89b4fa",
  mauve: "#cba6f7",
  peach: "#fab387",
  teal: "#94e2d5",
  lavender: "#b4befe",
} as const
