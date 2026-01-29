// Main App component with tab navigation and package management

import { useState, useCallback, useMemo } from "react"
import { useKeyboard, useRenderer } from "@opentui/react"
import { Header } from "./components/Header"
import { PackageList } from "./components/PackageList"
import { StatusBar } from "./components/StatusBar"
import { DetailPanel } from "./components/DetailPanel"
import { HelpModal } from "./components/HelpModal"
import { useBrewPackages } from "./hooks/useBrewPackages"
import { useFlakePackages } from "./hooks/useFlakePackages"
import { useFileWatcher } from "@dotfiles/shared/hooks"
import { getBrewInfo } from "./lib/brew"
import { getFlakePath } from "./lib/flake"
import type { Package, PackageType, PackageInfo } from "./lib/types"
import { colors } from "@dotfiles/shared/theme"

type AppMode = "normal" | "detail" | "help"
type SortMode = "name" | "status-asc" | "status-desc"

export function App() {
  const renderer = useRenderer()

  // State
  const [activeTab, setActiveTab] = useState<PackageType>("brews")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [selectedPackages, setSelectedPackages] = useState<Set<string>>(
    new Set()
  )
  const [mode, setMode] = useState<AppMode>("normal")
  const [sortMode, setSortMode] = useState<SortMode>("name")
  const [detailInfo, setDetailInfo] = useState<PackageInfo | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // Hooks for data
  const brew = useBrewPackages()
  const flake = useFlakePackages()

  // File watcher for auto-refresh
  const refreshAll = useCallback(async () => {
    await Promise.all([brew.refresh(), flake.refresh()])
  }, [brew.refresh, flake.refresh])

  const { isWatching } = useFileWatcher({ path: getFlakePath() }, refreshAll)

  // Compute package list based on active tab
  const packages: Package[] = useMemo(() => {
    let result: Package[] = []

    if (activeTab === "brews") {
      // Combine installed brews with flake brews
      const installedSet = new Set(brew.brews)
      const flakeSet = new Set(
        flake.brews.map((b) => b.split("/").pop() || b)
      )
      const flakeFullNames = new Map(
        flake.brews.map((b) => [b.split("/").pop() || b, b])
      )

      // All installed packages
      for (const name of brew.brews) {
        result.push({
          name,
          fullName: flakeFullNames.get(name) || name,
          status: flakeSet.has(name) ? "synced" : "extra",
          selected: selectedPackages.has(name),
        })
      }

      // Missing packages (in flake but not installed)
      for (const fullName of flake.brews) {
        const name = fullName.split("/").pop() || fullName
        if (!installedSet.has(name)) {
          result.push({
            name,
            fullName,
            status: "missing",
            selected: selectedPackages.has(name),
          })
        }
      }
    } else if (activeTab === "casks") {
      const installedSet = new Set(brew.casks)
      const flakeSet = new Set(flake.casks)

      for (const name of brew.casks) {
        result.push({
          name,
          fullName: name,
          status: flakeSet.has(name) ? "synced" : "extra",
          selected: selectedPackages.has(name),
        })
      }

      for (const name of flake.casks) {
        if (!installedSet.has(name)) {
          result.push({
            name,
            fullName: name,
            status: "missing",
            selected: selectedPackages.has(name),
          })
        }
      }
    } else if (activeTab === "masApps") {
      // Mac App Store apps - compare by ID since names can vary
      const installedMap = new Map(brew.masApps.map((a) => [a.id, a.name]))
      const flakeMap = new Map(flake.masApps.map((a) => [a.id, a.name]))

      // Installed apps
      for (const app of brew.masApps) {
        result.push({
          name: app.name,
          fullName: app.name,
          status: flakeMap.has(app.id) ? "synced" : "extra",
          selected: selectedPackages.has(app.name),
          masAppId: app.id,
        })
      }

      // Missing apps (in flake but not installed)
      for (const app of flake.masApps) {
        if (!installedMap.has(app.id)) {
          result.push({
            name: app.name,
            fullName: app.name,
            status: "missing",
            selected: selectedPackages.has(app.name),
            masAppId: app.id,
          })
        }
      }
    } else {
      // Nix packages (no "installed" check, just show what's in flake)
      for (const name of flake.nixpkgs) {
        result.push({
          name,
          fullName: name,
          status: "synced",
          selected: selectedPackages.has(name),
        })
      }
    }

    // Sort based on sort mode
    if (sortMode === "status-asc") {
      // Synced first, then extra, then missing
      const statusOrder: Record<string, number> = { synced: 0, extra: 1, missing: 2 }
      result.sort((a, b) => {
        const statusDiff = statusOrder[a.status] - statusOrder[b.status]
        if (statusDiff !== 0) return statusDiff
        return a.name.localeCompare(b.name)
      })
    } else if (sortMode === "status-desc") {
      // Missing first, then extra, then synced
      const statusOrder: Record<string, number> = { missing: 0, extra: 1, synced: 2 }
      result.sort((a, b) => {
        const statusDiff = statusOrder[a.status] - statusOrder[b.status]
        if (statusDiff !== 0) return statusDiff
        return a.name.localeCompare(b.name)
      })
    } else {
      // Name (alphabetical)
      result.sort((a, b) => a.name.localeCompare(b.name))
    }

    return result
  }, [
    activeTab,
    brew.brews,
    brew.casks,
    brew.masApps,
    flake.brews,
    flake.casks,
    flake.masApps,
    flake.nixpkgs,
    selectedPackages,
    sortMode,
  ])

  // Current package
  const currentPackage = packages[selectedIndex] || null

  // Handle keyboard input
  useKeyboard((key) => {
    // Global shortcuts
    if (key.name === "q" && mode === "normal") {
      renderer.destroy()
      return
    }

    if (key.ctrl && key.name === "c") {
      renderer.destroy()
      return
    }

    // Help mode - any key closes it
    if (mode === "help") {
      if (key.name === "escape" || key.name === "?" || key.name === "enter") {
        setMode("normal")
      }
      return
    }

    if (mode === "detail") {
      if (key.name === "escape" || key.name === "h") {
        setMode("normal")
        setDetailInfo(null)
      }
      return
    }

    // Normal mode shortcuts
    switch (key.name) {
      case "j":
      case "down":
        setSelectedIndex((i) => Math.min(packages.length - 1, i + 1))
        break

      case "k":
      case "up":
        setSelectedIndex((i) => Math.max(0, i - 1))
        break

      case "tab":
        setActiveTab((t) => {
          if (t === "brews") return "casks"
          if (t === "casks") return "masApps"
          if (t === "masApps") return "nixpkgs"
          return "brews"
        })
        setSelectedIndex(0)
        setSelectedPackages(new Set())
        break

      case "space":
        if (currentPackage) {
          setSelectedPackages((prev) => {
            const next = new Set(prev)
            if (next.has(currentPackage.name)) {
              next.delete(currentPackage.name)
            } else {
              next.add(currentPackage.name)
            }
            return next
          })
        }
        break

      case "s":
        // Toggle sort mode: name → status-asc → status-desc → name
        setSortMode((m) => {
          if (m === "name") return "status-asc"
          if (m === "status-asc") return "status-desc"
          return "name"
        })
        setSelectedIndex(0)
        break

      case "?":
        setMode("help")
        break

      case "r":
        refreshAll()
        break

      case "enter":
      case "l":
        if (currentPackage) {
          setMode("detail")
          setDetailLoading(true)
          getBrewInfo(currentPackage.name).then((info) => {
            setDetailInfo(info)
            setDetailLoading(false)
          })
        }
        break

      case "a":
        // Add selected/current packages to flake
        handleAdd()
        break

      case "d":
        // Delete selected/current packages from flake
        handleDelete()
        break

      case "escape":
        if (selectedPackages.size > 0) {
          setSelectedPackages(new Set())
        }
        break
    }
  })

  // Add packages to flake
  const handleAdd = useCallback(async () => {
    const toAdd =
      selectedPackages.size > 0
        ? packages.filter(
            (p) => selectedPackages.has(p.name) && p.status === "extra"
          )
        : currentPackage?.status === "extra"
          ? [currentPackage]
          : []

    for (const pkg of toAdd) {
      await flake.add(pkg.fullName, activeTab, pkg.masAppId)
    }
    setSelectedPackages(new Set())
  }, [selectedPackages, packages, currentPackage, flake, activeTab])

  // Delete packages from flake
  const handleDelete = useCallback(async () => {
    const toDelete =
      selectedPackages.size > 0
        ? packages.filter(
            (p) =>
              selectedPackages.has(p.name) &&
              (p.status === "synced" || p.status === "missing")
          )
        : currentPackage &&
            (currentPackage.status === "synced" ||
              currentPackage.status === "missing")
          ? [currentPackage]
          : []

    for (const pkg of toDelete) {
      await flake.remove(pkg.fullName, activeTab)
    }
    setSelectedPackages(new Set())
  }, [selectedPackages, packages, currentPackage, flake, activeTab])

  const isLoading = brew.loading || flake.loading

  return (
    <box
      flexDirection="column"
      backgroundColor={colors.base}
      width="100%"
      height="100%"
    >
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      <box flexDirection="row" flexGrow={1}>
        <box flexGrow={1} flexDirection="column">
          <PackageList
            packages={packages}
            selectedIndex={selectedIndex}
            onSelect={setSelectedIndex}
            focused={mode === "normal"}
          />
        </box>

        <DetailPanel
          visible={mode === "detail"}
          pkg={currentPackage}
          info={detailInfo}
          loading={detailLoading}
        />
      </box>

      <StatusBar
        packages={packages}
        packageType={activeTab}
        selectedCount={selectedPackages.size}
        isWatching={isWatching}
        isLoading={isLoading}
        sortMode={sortMode}
      />

      <HelpModal visible={mode === "help"} />
    </box>
  )
}
