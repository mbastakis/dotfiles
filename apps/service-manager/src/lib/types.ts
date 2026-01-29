// Service types for the service-manager TUI

export type ServiceStatus = "running" | "stopped" | "not_installed"

export interface Service {
  label: string
  configPath: string // Source path in ~/.config/service-manager/
  installedPath: string // Path in ~/Library/LaunchAgents/
  status: ServiceStatus
  enabled: boolean // Whether service is enabled in config
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

// TOML config file structure
export interface ServiceConfig {
  enabled: boolean
  service: {
    label: string
    program: string[]
    run_at_load?: boolean
    keep_alive?: boolean
    working_directory?: string
    environment?: Record<string, string>
  }
  logs?: {
    stdout?: string
    stderr?: string
  }
}

// Result type for config parsing with error details
export type ParseConfigResult =
  | { success: true; config: ServiceConfig }
  | { success: false; error: string }
