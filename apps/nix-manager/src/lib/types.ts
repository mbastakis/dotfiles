// Package types for the nix-manager TUI

export type PackageStatus = "synced" | "extra" | "missing"

export interface Package {
  name: string
  fullName: string // For tap packages like "oven-sh/bun/bun"
  status: PackageStatus
  selected: boolean
  masAppId?: number // Mac App Store app ID (for masApps)
}

export type PackageType = "brews" | "casks" | "masApps" | "nixpkgs"

export interface MasApp {
  name: string
  id: number
}

export interface PackageInfo {
  name: string
  version?: string
  description?: string
  homepage?: string
}

