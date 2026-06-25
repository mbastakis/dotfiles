import { mkdir, readFile, writeFile } from "node:fs/promises"
import { dirname, join } from "node:path"
import { getAgentDir, type ExtensionAPI } from "@earendil-works/pi-coding-agent"

type Settings = Record<string, unknown>
type PackageEntry = string | Record<string, unknown>

const DEFAULT_PACKAGE_SOURCE = "npm:@injaneity/pi-computer-use"
const PACKAGE_MARKER = "pi-computer-use"
const TOOL_SENTINELS = new Set([
	"list_apps",
	"list_windows",
	"screenshot",
	"click",
	"computer_actions",
])

function settingsPath(): string {
	return join(getAgentDir(), "settings.json")
}

function isRecord(value: unknown): value is Record<string, unknown> {
	return value !== null && typeof value === "object" && !Array.isArray(value)
}

function packageSource(entry: PackageEntry): string | undefined {
	if (typeof entry === "string") return entry
	return typeof entry.source === "string" ? entry.source : undefined
}

function isComputerUseEntry(entry: PackageEntry): boolean {
	return packageSource(entry)?.includes(PACKAGE_MARKER) ?? false
}

function packageEntries(settings: Settings): PackageEntry[] {
	return Array.isArray(settings.packages)
		? settings.packages.filter((entry): entry is PackageEntry => typeof entry === "string" || isRecord(entry))
		: []
}

async function readSettings(): Promise<Settings> {
	const path = settingsPath()

	try {
		const parsed = JSON.parse(await readFile(path, "utf8"))
		return isRecord(parsed) ? parsed : {}
	} catch (error) {
		if (isRecord(error) && error.code === "ENOENT") return {}
		throw error
	}
}

async function writeSettings(settings: Settings): Promise<void> {
	const path = settingsPath()
	await mkdir(dirname(path), { recursive: true })
	await writeFile(path, `${JSON.stringify(settings, null, 2)}\n`, "utf8")
}

function withComputerUseEnabled(settings: Settings): Settings {
	let found = false
	const packages = packageEntries(settings).map((entry) => {
		if (!isComputerUseEntry(entry)) return entry
		found = true

		if (typeof entry === "string") return entry

		const next = { ...entry }
		delete next.extensions
		return next
	})

	if (!found) packages.push(DEFAULT_PACKAGE_SOURCE)
	return { ...settings, packages }
}

function withComputerUseDisabled(settings: Settings): Settings {
	let found = false
	const packages = packageEntries(settings).map((entry) => {
		if (!isComputerUseEntry(entry)) return entry
		found = true

		if (typeof entry === "string") {
			return { source: entry, extensions: [] }
		}

		return { ...entry, source: packageSource(entry) ?? DEFAULT_PACKAGE_SOURCE, extensions: [] }
	})

	if (!found) packages.push({ source: DEFAULT_PACKAGE_SOURCE, extensions: [] })
	return { ...settings, packages }
}

function computerUseToolsLoaded(pi: ExtensionAPI): boolean {
	return pi.getAllTools().some((tool) => TOOL_SENTINELS.has(tool.name))
}

export default function computerUseToggle(pi: ExtensionAPI) {
	pi.registerCommand("computer-use-enable", {
		description: "Temporarily enable pi-computer-use tools in this Pi session",
		handler: async (_args, ctx) => {
			if (computerUseToolsLoaded(pi)) {
				ctx.ui.notify("pi-computer-use tools are already loaded in this session.", "info")
				return
			}

			const originalSettings = await readSettings()
			await writeSettings(withComputerUseEnabled(originalSettings))
			ctx.ui.notify("Enabling pi-computer-use for this session and reloading Pi resources...", "info")

			try {
				await ctx.reload()
			} finally {
				// Keep computer-use opt-in: the current runtime has already loaded it,
				// but future Pi sessions stay disabled unless the command is run again.
				await writeSettings(withComputerUseDisabled(await readSettings()))
			}
		},
	})

	pi.registerCommand("computer-use-disable", {
		description: "Disable pi-computer-use tools and reload Pi resources",
		handler: async (_args, ctx) => {
			await writeSettings(withComputerUseDisabled(await readSettings()))

			if (!computerUseToolsLoaded(pi)) {
				ctx.ui.notify("pi-computer-use tools are already disabled.", "info")
				return
			}

			ctx.ui.notify("Disabling pi-computer-use and reloading Pi resources...", "info")
			await ctx.reload()
		},
	})

	pi.registerCommand("computer-use-status", {
		description: "Show whether pi-computer-use tools are loaded in this session",
		handler: async (_args, ctx) => {
			const loaded = computerUseToolsLoaded(pi)
			ctx.ui.notify(
				loaded
					? "pi-computer-use tools are loaded for this session. Use /computer-use-disable to turn them off."
					: "pi-computer-use tools are not loaded. Use /computer-use-enable to opt in for this session.",
				"info",
			)
		},
	})
}
