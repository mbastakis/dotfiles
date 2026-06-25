import { execFile } from "node:child_process"
import { existsSync, readFileSync } from "node:fs"
import { chmod, mkdir, writeFile } from "node:fs/promises"
import { homedir, tmpdir } from "node:os"
import { basename, dirname, join, relative, resolve } from "node:path"
import { pathToFileURL } from "node:url"
import { buildSessionContext } from "@earendil-works/pi-coding-agent"
import type {
	BuildSystemPromptOptions,
	ExtensionAPI,
	ExtensionCommandContext,
} from "@earendil-works/pi-coding-agent"
import { Key, matchesKey, truncateToWidth } from "@earendil-works/pi-tui"

/**
 * Context Inspector
 * =================
 *
 * This Pi extension provides the `/context` command.
 *
 * It builds a read-only snapshot of the current Pi session and renders that
 * snapshot in a small TUI overlay. The snapshot includes:
 *
 * - session metadata
 * - prompt resources
 * - slash commands
 * - registered and active tools
 * - raw branch entries
 * - resolved model context
 * - a request preview
 * - approximate token/category usage
 *
 * Interaction model:
 *
 * 1. Section list
 *    - Up/Down moves between sections.
 *    - Enter/Right opens the selected section's item list.
 *
 * 2. Item list
 *    - Up/Down moves between items.
 *    - Enter/Right opens the selected item detail.
 *    - Left returns to the section list.
 *
 * 3. Item detail
 *    - Up/Down scrolls the full item body.
 *    - Left returns to the item list.
 *
 * Press `b` in any view to write a rich HTML snapshot to the OS temp directory and open it in your browser.
 * Press `e` in any view to export the snapshot to the OS temp directory.
 *
 * Security note:
 * Snapshot exports may contain private prompts, messages, tool calls, context
 * files, secrets, and project data. Treat exported files as local-only debugging
 * artifacts unless explicitly reviewed and redacted.
 */

type AnyRecord = Record<string, unknown>

type PromptCache = {
	systemPrompt: string
	options: SnapshotPromptOptions
}

type SnapshotPromptOptions = {
	customPrompt?: string
	selectedTools?: string[]
	toolSnippets?: Record<string, string>
	promptGuidelines?: string[]
	appendSystemPrompt?: string
	cwd: string
	contextFiles?: Array<{ path: string; content: string }>
	skills?: Array<AnyRecord>
}

type SnapshotItem = {
	id: string
	title: string
	sourceType: string
	sourceId?: string
	preview: string
	body: string
	tokenEstimate: number
	meta?: AnyRecord
}

type SnapshotSection = {
	id: string
	title: string
	summary: string
	items: SnapshotItem[]
	tokenEstimate: number
}

type UsageCategory = {
	id: string
	label: string
	symbol: string
	tokens: number
	percentOfWindow?: number
}

type CompactionSettingsSnapshot = {
	reserveTokens?: number
	keepRecentTokens?: number
}

type ContextSnapshot = {
	generatedAt: string
	cwd: string
	sessionFile?: string
	sessionId?: string
	sessionName?: string
	model?: string
	thinkingLevel?: string
	usage?: AnyRecord
	usageCategories: UsageCategory[]
	compaction: CompactionSettingsSnapshot
	sections: SnapshotSection[]
}

type InspectorView = "sections" | "items" | "detail"

type InspectorState = {
	view: InspectorView
	selectedSection: number
	selectedItem: number
	detailScroll: number
}

const SNAPSHOT_WARNING =
	"This snapshot may contain private prompts, messages, tool calls, file contents, and secrets. Do not commit or share without review."

const DEFAULT_EXPORT_DIR = "pi-context-snapshots"

const FREE_GLYPH = "⬡"
const RESERVED_GLYPH = "⬢"
const USED_GLYPH = "⬢"

/**
 * Keep only the prompt options that are safe to snapshot structurally.
 *
 * We clone arrays/objects so the rendered snapshot remains stable even if Pi
 * mutates internal prompt state after the command starts.
 */
function clonePromptOptions(options: BuildSystemPromptOptions | undefined, cwd: string): SnapshotPromptOptions {
	return {
		customPrompt: options?.customPrompt,
		selectedTools: options?.selectedTools ? [...options.selectedTools] : undefined,
		toolSnippets: options?.toolSnippets ? { ...options.toolSnippets } as Record<string, string> : undefined,
		promptGuidelines: options?.promptGuidelines ? [...options.promptGuidelines] : undefined,
		appendSystemPrompt: options?.appendSystemPrompt,
		cwd: options?.cwd ?? cwd,
		contextFiles: options?.contextFiles?.map((file) => ({ path: file.path, content: file.content })),

		skills: options?.skills?.map((skill) => ({ ...(skill as unknown as AnyRecord) })),
	}
}

/**
 * Very rough token estimate used only for UI hints.
 *
 * Do not treat this as model-accurate accounting. It intentionally avoids a
 * tokenizer dependency because the inspector should stay lightweight.
 */
function approxTokens(text: string | undefined | null): number {
	const normalized = String(text ?? "")
	if (!normalized.trim()) return 0
	return Math.max(1, Math.ceil(normalized.length / 4))
}

function summarizeText(text: string | undefined | null, maxLength = 180): string {
	const normalized = String(text ?? "")
	const collapsed = normalized.replace(/\s+/g, " ").trim()
	if (collapsed.length <= maxLength) return collapsed || "(empty)"
	return `${collapsed.slice(0, Math.max(0, maxLength - 1))}…`
}

function safeJson(value: unknown): string {
	try {
		const serialized = JSON.stringify(value, null, 2)
		return typeof serialized === "string" ? serialized : String(value)
	} catch {
		return String(value)
	}
}

/**
 * Remove ANSI escape sequences and control characters from content that came
 * from prompts, files, messages, or tool calls.
 *
 * This prevents prompt/file content from controlling the terminal UI.
 */
function sanitizeForTerminal(text: string): string {
	return String(text ?? "")
		.replace(/\x1b\[[0-?]*[ -/]*[@-~]/g, "")
		.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, "")
}

/**
 * Strip ANSI escape sequences used by our own color rendering.
 *
 * This is used for width calculations. We do not sanitize here because we still
 * want our generated color codes to reach the terminal.
 */
function stripAnsi(text: string): string {
	return String(text ?? "").replace(/\x1b\[[0-?]*[ -/]*[@-~]/g, "")
}

/**
 * Approximate visible width.
 *
 * Pi already provides truncateToWidth, but we still need a tiny helper for
 * padding ANSI-colored strings without counting escape codes as visible chars.
 */
function visibleWidth(text: string): number {
	return stripAnsi(text).length
}

function padVisibleEnd(text: string, targetWidth: number): string {
	return `${text}${" ".repeat(Math.max(0, targetWidth - visibleWidth(text)))}`
}

function extractText(content: unknown, options: { includeThinking?: boolean } = {}): string {
	if (typeof content === "string") return sanitizeForTerminal(content)
	if (!Array.isArray(content)) return sanitizeForTerminal(safeJson(content))

	const lines: string[] = []
	for (const part of content) {
		if (!part || typeof part !== "object") continue
		const block = part as AnyRecord

		if (block.type === "text" && typeof block.text === "string") {
			lines.push(block.text)
			continue
		}

		if (block.type === "thinking" && typeof block.thinking === "string") {
			lines.push(options.includeThinking ? `[thinking] ${block.thinking}` : "[thinking] (redacted)")
			continue
		}

		if (block.type === "toolCall") {
			const name = typeof block.name === "string" ? block.name : "tool"
			lines.push(`[toolCall] ${name} ${safeJson(block.arguments ?? {})}`)
			continue
		}

		if (block.type === "image") {
			const mime = typeof block.mimeType === "string" ? block.mimeType : "image"
			lines.push(`[image] ${mime}`)
			continue
		}
	}

	return sanitizeForTerminal(lines.length > 0 ? lines.join("\n") : safeJson(content))
}

function makeItem(
	id: string,
	title: string,
	sourceType: string,
	body: string,
	meta?: AnyRecord,
	sourceId?: string,
	preview?: string,
): SnapshotItem {
	const normalizedBody = sanitizeForTerminal(String(body ?? ""))
	return {
		id,
		title: sanitizeForTerminal(title),
		sourceType: sanitizeForTerminal(sourceType),
		sourceId: sourceId ? sanitizeForTerminal(sourceId) : undefined,
		body: normalizedBody,
		preview: sanitizeForTerminal(preview ?? summarizeText(normalizedBody)),
		tokenEstimate: approxTokens(normalizedBody),
		meta,
	}
}

function formatUsage(usage: { percent?: number | null; contextWindow?: number | null } | undefined): string {
	if (!usage) return "ctx ?"
	const percent = typeof usage.percent === "number" ? `${Math.round(usage.percent)}%` : "?"
	const window = typeof usage.contextWindow === "number" ? `${Math.round(usage.contextWindow / 1000)}k` : "?"
	return `ctx ${percent}/${window}`
}

function formatTokenCount(tokens: number | null | undefined): string {
	if (typeof tokens !== "number" || !Number.isFinite(tokens)) return "?"
	if (tokens >= 1000) return `${(tokens / 1000).toFixed(tokens >= 10000 ? 0 : 1)}k`
	return `${Math.round(tokens)}`
}

function buildUsageBar(percent: number | null | undefined, width = 18): string {
	if (typeof percent !== "number" || !Number.isFinite(percent)) {
		return `[${"·".repeat(width)}]`
	}

	const filled = Math.max(0, Math.min(width, Math.round((percent / 100) * width)))
	return `[${"█".repeat(filled)}${"·".repeat(width - filled)}]`
}

function categoryColor(categoryId: string): string {
	switch (categoryId) {
		case "system-prompt":
			return "\x1b[38;5;45m"
		case "base-system-prompt":
			return "\x1b[38;5;39m"
		case "system-tools":
			return "\x1b[38;5;82m"
		case "mcp-tools":
			return "\x1b[38;5;213m"
		case "memory-files":
			return "\x1b[38;5;117m"
		case "skills":
			return "\x1b[38;5;220m"
		case "messages":
			return "\x1b[38;5;255m"
		case "other":
			return "\x1b[38;5;203m"
		case "free":
			return "\x1b[38;5;250m"
		case "reserved":
			// Reserved context is unavailable capacity. Use a filled grey
			// hexagon so it reads as blocked/unavailable while staying quieter
			// than active token categories.
			return "\x1b[38;5;246m"
		default:
			return ""
	}
}

function colorize(text: string, categoryId: string): string {
	const color = categoryColor(categoryId)
	if (!color) return text
	return `${color}${text}\x1b[0m`
}

function bold(text: string): string {
	return `\x1b[1m${text}\x1b[22m`
}

function readJsonFile(path: string): AnyRecord | undefined {
	try {
		if (!existsSync(path)) return undefined
		const parsed = JSON.parse(readFileSync(path, "utf8"))
		return parsed && typeof parsed === "object" ? (parsed as AnyRecord) : undefined
	} catch {
		return undefined
	}
}

/**
 * Read compaction settings from global/project config.
 *
 * `reserveTokens` represents unavailable capacity and is shown in the usage map.
 * `keepRecentTokens` is retained in the exported snapshot for debugging, but it
 * is not rendered in the map/legend because it is a retention policy, not
 * reserved context-window capacity.
 */
function getCompactionSettings(ctx: ExtensionCommandContext): CompactionSettingsSnapshot {
	const globalSettings = readJsonFile(join(homedir(), ".pi", "agent", "settings.json"))
	const projectSettings = readJsonFile(join(ctx.cwd, ".pi", "settings.json"))

	const globalCompaction = globalSettings?.compaction as AnyRecord | undefined
	const projectCompaction = projectSettings?.compaction as AnyRecord | undefined

	const reserveTokens =
		typeof projectCompaction?.reserveTokens === "number"
			? projectCompaction.reserveTokens
			: typeof globalCompaction?.reserveTokens === "number"
				? globalCompaction.reserveTokens
				: undefined

	const keepRecentTokens =
		typeof projectCompaction?.keepRecentTokens === "number"
			? projectCompaction.keepRecentTokens
			: typeof globalCompaction?.keepRecentTokens === "number"
				? globalCompaction.keepRecentTokens
				: undefined

	return { reserveTokens, keepRecentTokens }
}

function formatModel(model: unknown): string {
	if (!model || typeof model !== "object") return "no-model"

	const record = model as AnyRecord
	const provider = typeof record.provider === "string" ? record.provider : ""
	const id = typeof record.id === "string" ? record.id : typeof record.modelId === "string" ? record.modelId : ""

	if (provider && id) return `${provider}/${id}`
	return id || provider || "no-model"
}

function formatSectionSummary(section: SnapshotSection): string {
	const count = section.items.length
	const tokens = section.tokenEstimate
	return `${count} item${count === 1 ? "" : "s"}${tokens > 0 ? ` • ~${tokens} tok` : ""}`
}

/**
 * Best-effort category breakdown for the usage legend.
 *
 * Pi provides total context usage. The category breakdown here is reconstructed
 * from cached prompt inputs and resolved messages, so it should be treated as
 * a diagnostic estimate rather than exact billing/token accounting.
 */
function estimateUsageCategories(
	ctx: ExtensionCommandContext,
	pi: ExtensionAPI,
	cache: PromptCache | undefined,
	resolvedTokens: number,
	compaction: CompactionSettingsSnapshot,
): UsageCategory[] {
	const usage = ctx.getContextUsage()
	const contextWindow = usage?.contextWindow
	const usedTokens = usage?.tokens
	const options = cache?.options
	const toolSourceByName = new Map(pi.getAllTools().map((tool) => [tool.name, tool.sourceInfo.source]))

	let promptResourceTokens = 0
	let systemToolTokens = 0
	let mcpToolTokens = 0
	let memoryFileTokens = 0
	let skillTokens = 0

	if (options) {
		if (options.customPrompt) promptResourceTokens += approxTokens(options.customPrompt)
		if (options.appendSystemPrompt) promptResourceTokens += approxTokens(options.appendSystemPrompt)
		if (options.promptGuidelines?.length) promptResourceTokens += approxTokens(options.promptGuidelines.join("\n"))

		for (const file of options.contextFiles ?? []) {
			memoryFileTokens += approxTokens(file.content)
		}

		for (const skill of options.skills ?? []) {
			const body = [
				typeof skill.description === "string" ? skill.description : "",
				typeof skill.filePath === "string" ? `file: ${skill.filePath}` : "",
				typeof skill.source === "string" ? `source: ${skill.source}` : "",
			]
				.filter(Boolean)
				.join("\n")

			skillTokens += approxTokens(body || safeJson(skill))
		}

		for (const [toolName, snippet] of Object.entries(options.toolSnippets ?? {})) {
			const source = toolSourceByName.get(toolName)
			if (source === "mcp") mcpToolTokens += approxTokens(snippet)
			else systemToolTokens += approxTokens(snippet)
		}
	} else {
		promptResourceTokens = approxTokens(ctx.getSystemPrompt())
	}

	const fullSystemPromptTokens = approxTokens(cache?.systemPrompt ?? ctx.getSystemPrompt())
	const baseSystemPromptTokens = Math.max(0, fullSystemPromptTokens - promptResourceTokens)

	const categories: UsageCategory[] = [
		{ id: "system-prompt", label: "Prompt resources", symbol: "S", tokens: promptResourceTokens },
		{ id: "base-system-prompt", label: "Base system prompt", symbol: "B", tokens: baseSystemPromptTokens },
		{ id: "system-tools", label: "System tools", symbol: "T", tokens: systemToolTokens },
		{ id: "mcp-tools", label: "MCP tools", symbol: "M", tokens: mcpToolTokens },
		{ id: "memory-files", label: "Memory files", symbol: "F", tokens: memoryFileTokens },
		{ id: "skills", label: "Skills", symbol: "K", tokens: skillTokens },
		{ id: "messages", label: "Messages", symbol: "G", tokens: resolvedTokens },
	]
		.filter((category) => category.tokens > 0)
		.map((category) => ({
			...category,
			percentOfWindow: contextWindow ? (category.tokens / contextWindow) * 100 : undefined,
		}))

	if (typeof usedTokens === "number") {
		const categorizedTokens = categories.reduce((sum: number, category: UsageCategory) => sum + category.tokens, 0)
		const effectiveUsedTokens = Math.max(usedTokens, categorizedTokens)
		const unattributedTokens = Math.max(0, effectiveUsedTokens - categorizedTokens)

		if (unattributedTokens > 0) {
			categories.push({
				id: "other",
				label: "Other / hidden",
				symbol: "X",
				tokens: unattributedTokens,
				percentOfWindow: contextWindow ? (unattributedTokens / contextWindow) * 100 : undefined,
			})
		}

		const reserveTokens = Math.max(0, Math.min(compaction.reserveTokens ?? 0, contextWindow ?? 0))
		const freeTokens = contextWindow ? Math.max(0, contextWindow - effectiveUsedTokens - reserveTokens) : 0

		if (freeTokens > 0) {
			categories.push({
				id: "free",
				label: "Free space",
				symbol: FREE_GLYPH,
				tokens: freeTokens,
				percentOfWindow: contextWindow ? (freeTokens / contextWindow) * 100 : undefined,
			})
		}

		if (reserveTokens > 0 && contextWindow) {
			categories.push({
				id: "reserved",
				label: "Reserved space",
				symbol: "⬢",
				tokens: reserveTokens,
				percentOfWindow: (reserveTokens / contextWindow) * 100,
			})
		}
	}

	return categories
}

/**
 * Render a 10x10 proportional usage grid.
 *
 * Each cell is one percent of the model context window. Rounding uses largest
 * remainder allocation so tiny categories still show up when possible.
 */
function buildUsageGrid(categories: UsageCategory[]): string[] {
	if (categories.length === 0) return []

	const totalCells = 100
	const exactCells = categories.map((category) => {
		const exact = typeof category.percentOfWindow === "number" ? (category.percentOfWindow / 100) * totalCells : 0
		return { category, exact, cells: Math.floor(exact), remainder: exact - Math.floor(exact) }
	})

	let assigned = exactCells.reduce((sum: number, entry: { category: UsageCategory; exact: number; cells: number; remainder: number }) => sum + entry.cells, 0)
	for (const entry of [...exactCells].sort((a, b) => b.remainder - a.remainder)) {
		if (assigned >= totalCells) break
		entry.cells += 1
		assigned += 1
	}

	const glyphFor = (category: UsageCategory) => {
		if (category.id === "free") return FREE_GLYPH
		if (category.id === "reserved") return RESERVED_GLYPH
		return USED_GLYPH
	}
	const chars = exactCells.flatMap((entry) => Array(entry.cells).fill(entry.category)).slice(0, totalCells)

	while (chars.length < totalCells) {
		chars.push({ id: "free", label: "Free space", symbol: FREE_GLYPH, tokens: 0 })
	}

	const lines: string[] = []
	for (let row = 0; row < 10; row++) {
		const rowCells = chars.slice(row * 10, row * 10 + 10)
		lines.push(rowCells.map((category) => colorize(glyphFor(category), category.id)).join(" "))
	}

	return lines
}

function summarizePromptOptions(options: SnapshotPromptOptions | undefined, fallbackSystemPrompt?: string): SnapshotSection {
	const items: SnapshotItem[] = []

	if (!options && !fallbackSystemPrompt) {
		return {
			id: "system",
			title: "System prompt & resources",
			summary: "No prompt metadata cached yet",
			items,
			tokenEstimate: 0,
		}
	}

	if (options?.customPrompt) {
		items.push(makeItem("customPrompt", "Custom system prompt", "system", options.customPrompt, { kind: "customPrompt" }))
	}

	if (options?.appendSystemPrompt) {
		items.push(makeItem("appendSystemPrompt", "Appended system prompt", "system", options.appendSystemPrompt, { kind: "appendSystemPrompt" }))
	}

	if (options?.contextFiles?.length) {
		for (const file of options.contextFiles) {
			items.push(makeItem(`context:${file.path}`, file.path, "context-file", file.content, { path: file.path }, file.path))
		}
	}

	if (options?.skills?.length) {
		for (const skill of options.skills) {
			const title = typeof skill.name === "string" ? skill.name : typeof skill.filePath === "string" ? skill.filePath : "skill"
			const body = [
				typeof skill.description === "string" ? skill.description : "",
				typeof skill.filePath === "string" ? `file: ${skill.filePath}` : "",
				typeof skill.source === "string" ? `source: ${skill.source}` : "",
			]
				.filter(Boolean)
				.join("\n")

			items.push(makeItem(`skill:${title}`, title, "skill", body || safeJson(skill), skill, typeof skill.filePath === "string" ? skill.filePath : undefined))
		}
	}

	if (options?.selectedTools?.length) {
		items.push(makeItem("selectedTools", "Selected tools", "tools", options.selectedTools.join(", "), { count: options.selectedTools.length }))
	}

	if (options?.toolSnippets) {
		for (const [tool, snippet] of Object.entries(options.toolSnippets)) {
			items.push(makeItem(`toolSnippet:${tool}`, `Tool snippet: ${tool}`, "tool-snippet", snippet, { tool }))
		}
	}

	if (options?.promptGuidelines?.length) {
		items.push(
			makeItem(
				"promptGuidelines",
				"Prompt guidelines",
				"guideline",
				options.promptGuidelines.map((g) => `• ${g}`).join("\n"),
				{ count: options.promptGuidelines.length },
			),
		)
	}

	// This makes the full generated prompt directly inspectable.
	// It also fixes the common case where selecting prompt resources only showed
	// partial prompt pieces rather than the complete prompt sent to the model.
	if (fallbackSystemPrompt) {
		items.unshift(
			makeItem(
				"currentSystemPrompt",
				"Full generated system prompt",
				"system",
				fallbackSystemPrompt,
				{ kind: "currentSystemPrompt" },
			),
		)
	}

	return {
		id: "system",
		title: "System prompt & resources",
		summary: items.length > 0 ? `${items.length} loaded resource item(s)` : "No loaded resource metadata cached",
		items,
		tokenEstimate: items.reduce((sum, item) => sum + item.tokenEstimate, 0),
	}
}

function buildCommandsSection(pi: ExtensionAPI): SnapshotSection {
	const items = pi.getCommands().map((command) => {
		const sourceInfo = command.sourceInfo
		const source = `${sourceInfo.source}/${sourceInfo.scope}`

		const body = [
			command.description ?? "(no description)",
			`source: ${source}`,
			sourceInfo.path ? `path: ${sourceInfo.path}` : "",
			sourceInfo.origin ? `origin: ${sourceInfo.origin}` : "",
			sourceInfo.baseDir ? `baseDir: ${sourceInfo.baseDir}` : "",
		]
			.filter(Boolean)
			.join("\n")

		return makeItem(`command:${command.name}`, `/${command.name}`, sourceInfo.source, body, { sourceInfo })
	})

	return {
		id: "commands",
		title: "Slash commands",
		summary: items.length > 0 ? `${items.length} command(s)` : "No commands loaded",
		items,
		tokenEstimate: items.reduce((sum: number, item: SnapshotItem) => sum + item.tokenEstimate, 0),
	}
}

function buildToolsSection(pi: ExtensionAPI): SnapshotSection {
	const active = new Set(pi.getActiveTools())

	const items = pi.getAllTools().map((tool) => {
		const sourceInfo = tool.sourceInfo
		const body = [
			tool.description ?? "(no description)",
			`source: ${sourceInfo.source}`,
			`active: ${active.has(tool.name) ? "yes" : "no"}`,
			sourceInfo.path ? `path: ${sourceInfo.path}` : "",
			sourceInfo.scope ? `scope: ${sourceInfo.scope}` : "",
			sourceInfo.origin ? `origin: ${sourceInfo.origin}` : "",
		]
			.filter(Boolean)
			.join("\n")

		return makeItem(`tool:${tool.name}`, tool.name, sourceInfo.source, body, { sourceInfo, active: active.has(tool.name) })
	})

	return {
		id: "tools",
		title: "Tool registry & active tools",
		summary: `${active.size}/${items.length} active`,
		items,
		tokenEstimate: items.reduce((sum, item) => sum + item.tokenEstimate, 0),
	}
}

function buildSessionBranchSection(ctx: ExtensionCommandContext): SnapshotSection {
	const branch = ctx.sessionManager.getBranch()

	const items = branch.map((entry) => {
		const raw = entry as unknown as AnyRecord
		let title: string = entry.type
		let body = ""
		const meta: AnyRecord = {}

		if (entry.type === "message" && raw.message) {
			const message = raw.message as AnyRecord
			const role = typeof message.role === "string" ? message.role : "message"
			title = `${role}`
			body = extractText(message.content)
			meta.role = role
			if (typeof message.toolName === "string") meta.toolName = message.toolName
			if (typeof message.toolCallId === "string") meta.toolCallId = message.toolCallId
		}

		if (entry.type === "compaction") {
			title = "compaction"
			body = typeof raw.summary === "string" ? raw.summary : safeJson(raw)
			if (typeof raw.firstKeptEntryId === "string") meta.firstKeptEntryId = raw.firstKeptEntryId
			if (typeof raw.tokensBefore === "number") meta.tokensBefore = raw.tokensBefore
		}

		if (entry.type === "branch_summary") {
			title = "branch summary"
			body = typeof raw.summary === "string" ? raw.summary : safeJson(raw)
			if (typeof raw.fromId === "string") meta.fromId = raw.fromId
		}

		if (entry.type === "custom") {
			title = typeof raw.customType === "string" ? `custom:${raw.customType}` : "custom"
			body = safeJson(raw.data)
			if (typeof raw.customType === "string") meta.customType = raw.customType
		}

		if (entry.type === "label") {
			title = `label:${typeof raw.label === "string" ? raw.label : "(unset)"}`
			body = `target: ${String(raw.targetId ?? "")}`
			meta.targetId = raw.targetId
		}

		if (entry.type === "model_change") {
			title = "model change"
			body = `${String(raw.provider ?? "")} / ${String(raw.modelId ?? "")}`.trim()
		}

		if (entry.type === "thinking_level_change") {
			title = "thinking level change"
			body = String(raw.thinkingLevel ?? "")
		}

		if (!body) body = safeJson(raw)

		return makeItem(String(entry.id), title, entry.type, body, meta)
	})

	return {
		id: "session",
		title: "Session branch",
		summary: `${items.length} entry(ies) on current branch`,
		items,
		tokenEstimate: items.reduce((sum: number, item: SnapshotItem) => sum + item.tokenEstimate, 0),
	}
}

function buildResolvedContextSection(ctx: ExtensionCommandContext): SnapshotSection {
	const resolved = buildSessionContext(ctx.sessionManager.getBranch(), ctx.sessionManager.getLeafId())

	const items = resolved.messages.map((message, index) => {
		const raw = message as unknown as AnyRecord
		const role = typeof raw.role === "string" ? raw.role : "message"
		const title = `${index + 1}. ${role}`
		const body = extractText(raw.content)
		const meta: AnyRecord = {}

		if (typeof raw.provider === "string") meta.provider = raw.provider
		if (typeof raw.model === "string") meta.model = raw.model
		if (typeof raw.stopReason === "string") meta.stopReason = raw.stopReason
		if (typeof raw.toolName === "string") meta.toolName = raw.toolName
		if (typeof raw.toolCallId === "string") meta.toolCallId = raw.toolCallId

		return makeItem(`resolved:${index}`, title, role, body, meta)
	})

	return {
		id: "resolved",
		title: "Resolved model context",
		summary: `${items.length} message(s) after session resolution`,
		items,
		tokenEstimate: items.reduce((sum: number, item: SnapshotItem) => sum + item.tokenEstimate, 0),
	}
}

function buildRequestPreviewSection(ctx: ExtensionCommandContext, pi: ExtensionAPI, cache: PromptCache | undefined): SnapshotSection {
	const sessionContext = buildSessionContext(ctx.sessionManager.getBranch(), ctx.sessionManager.getLeafId())
	const systemPrompt = cache?.systemPrompt ?? ctx.getSystemPrompt()
	const usage = ctx.getContextUsage()
	const currentModel = formatModel(ctx.model)
	const activeTools = pi.getActiveTools()

	const body = [
		`model: ${currentModel}`,
		`thinking: ${sessionContext.thinkingLevel}`,
		`messages: ${sessionContext.messages.length}`,
		`system prompt chars: ${systemPrompt.length}`,
		`usage: ${formatUsage(usage)}`,
		activeTools.length ? `active tools: ${activeTools.join(", ")}` : "active tools: (none)",
		cache?.options.selectedTools?.length ? `selected tools: ${cache.options.selectedTools.join(", ")}` : "selected tools: (not cached)",
		cache?.options.contextFiles?.length ? `context files: ${cache.options.contextFiles.length}` : "context files: (not cached)",
		cache?.options.skills?.length ? `skills: ${cache.options.skills.length}` : "skills: (not cached)",
	]
		.filter(Boolean)
		.join("\n")

	return {
		id: "request",
		title: "Request preview",
		summary: "Best-effort reconstruction of the current request",
		items: [
			makeItem("request-preview", "Request preview", "preview", body, {
				model: currentModel,
				messageCount: sessionContext.messages.length,
				systemPromptChars: systemPrompt.length,
				usage,
				activeTools,
			}),
		],
		tokenEstimate: approxTokens(systemPrompt) + approxTokens(body),
	}
}

function buildOverviewSection(ctx: ExtensionCommandContext, sessionContext: ReturnType<typeof buildSessionContext>): SnapshotSection {
	return {
		id: "overview",
		title: "Overview",
		summary: `${formatModel(ctx.model)} • ${formatUsage(ctx.getContextUsage())}`,
		items: [
			makeItem("cwd", "Working directory", "meta", ctx.cwd, { kind: "cwd" }),
			makeItem("sessionFile", "Session file", "meta", ctx.sessionManager.getSessionFile() ?? "(ephemeral)", { kind: "sessionFile" }),
			makeItem("sessionId", "Session id", "meta", ctx.sessionManager.getSessionId(), { kind: "sessionId" }),
			makeItem("model", "Model", "meta", formatModel(ctx.model), { kind: "model" }),
			makeItem("thinking", "Thinking level", "meta", String(sessionContext.thinkingLevel), { kind: "thinking" }),
			makeItem("usage", "Context usage", "meta", formatUsage(ctx.getContextUsage()), { kind: "usage" }),
		],
		tokenEstimate: 0,
	}
}

/**
 * Build an immutable snapshot once per command invocation.
 *
 * The UI only reads this snapshot; it does not repeatedly query Pi state while
 * the user navigates. This keeps the inspector stable and easier to debug.
 */
function buildSnapshot(ctx: ExtensionCommandContext, pi: ExtensionAPI, cache: PromptCache | undefined): ContextSnapshot {
	const sessionContext = buildSessionContext(ctx.sessionManager.getBranch(), ctx.sessionManager.getLeafId())
	const resolvedSection = buildResolvedContextSection(ctx)
	const compaction = getCompactionSettings(ctx)

	const sections = [
		buildOverviewSection(ctx, sessionContext),
		summarizePromptOptions(cache?.options, cache?.systemPrompt ?? ctx.getSystemPrompt()),
		buildCommandsSection(pi),
		buildToolsSection(pi),
		buildSessionBranchSection(ctx),
		resolvedSection,
		buildRequestPreviewSection(ctx, pi, cache),
	].map((section) => ({
		...section,
		tokenEstimate: section.items.reduce((sum: number, item: SnapshotItem) => sum + item.tokenEstimate, 0),
	}))

	return {
		generatedAt: new Date().toISOString(),
		cwd: ctx.cwd,
		sessionFile: ctx.sessionManager.getSessionFile(),
		sessionId: ctx.sessionManager.getSessionId(),
		sessionName: ctx.sessionManager.getSessionName(),
		model: formatModel(ctx.model),
		thinkingLevel: sessionContext.thinkingLevel,
		usage: ctx.getContextUsage() as unknown as AnyRecord,
		usageCategories: estimateUsageCategories(ctx, pi, cache, resolvedSection.tokenEstimate, compaction),
		compaction,
		sections,
	}
}

function clampLineToWidth(line: string, width: number): string {
	return truncateToWidth(String(line ?? ""), width, "")
}

function wrapInspectorLine(line: string, width: number): string[] {
	const normalized = sanitizeForTerminal(String(line ?? ""))
	if (width <= 0) return [normalized]

	const wrapped: string[] = []

	for (const paragraph of normalized.split(/\r?\n/)) {
		if (paragraph.length === 0) {
			wrapped.push("")
			continue
		}

		const indent = paragraph.match(/^\s*/)?.[0] ?? ""
		let remaining = paragraph.slice(indent.length)
		const available = Math.max(1, width - indent.length)

		while (remaining.length > available) {
			let breakAt = remaining.lastIndexOf(" ", available)
			if (breakAt <= 0) breakAt = available

			let chunk = remaining.slice(0, breakAt).trimEnd()
			if (!chunk) chunk = remaining.slice(0, available)

			wrapped.push(`${indent}${chunk}`)
			remaining = remaining.slice(breakAt).trimStart()
		}

		wrapped.push(`${indent}${remaining}`)
	}

	return wrapped
}

function sectionAt(snapshot: ContextSnapshot, state: InspectorState): SnapshotSection | undefined {
	return snapshot.sections[state.selectedSection]
}

function itemAt(snapshot: ContextSnapshot, state: InspectorState): SnapshotItem | undefined {
	const section = sectionAt(snapshot, state)
	return section?.items[state.selectedItem]
}

function renderUsageHeader(snapshot: ContextSnapshot, width: number): string[] {
	const lines: string[] = []
	const clamp = (s: string) => clampLineToWidth(s, width)
	const rawUsageTokens = typeof snapshot.usage?.tokens === "number" ? snapshot.usage.tokens : null
	const usageWindow = typeof snapshot.usage?.contextWindow === "number" ? snapshot.usage.contextWindow : null
	const estimatedUsedTokens = snapshot.usageCategories
		.filter((category: UsageCategory) => category.id !== "free" && category.id !== "reserved")
		.reduce((sum: number, category: UsageCategory) => sum + category.tokens, 0)

	const usageTokens = Math.max(rawUsageTokens ?? 0, estimatedUsedTokens)
	const usagePercent = usageWindow ? (usageTokens / usageWindow) * 100 : null
	const visibleBreakdown = snapshot.usageCategories.filter((category) => category.id !== "free" && category.id !== "reserved")
	const usageGrid = buildUsageGrid(snapshot.usageCategories)
	const freeSpace = snapshot.usageCategories.find((category) => category.id === "free")

	lines.push(clamp(bold(`Context Usage • ${snapshot.model ?? "no-model"}`)))
	lines.push("")
	lines.push(clamp(`${buildUsageBar(usagePercent)} ~${formatTokenCount(usageTokens)} / ${formatTokenCount(usageWindow)} tokens${typeof usagePercent === "number" ? ` (${Math.round(usagePercent)}%)` : ""}`))

	const sidebarLines = [bold("Estimated usage by category"), ""]
	for (const category of visibleBreakdown) {
		const percentText = typeof category.percentOfWindow === "number" ? ` (${category.percentOfWindow.toFixed(1)}%)` : ""
		const marker = category.id === "free" ? FREE_GLYPH : USED_GLYPH
		sidebarLines.push(`${colorize(marker, category.id)} ${category.label}: ${formatTokenCount(category.tokens)} tokens${percentText}`)
	}

	if (freeSpace) {
		const percentText = typeof freeSpace.percentOfWindow === "number" ? ` (${freeSpace.percentOfWindow.toFixed(1)}%)` : ""
		sidebarLines.push(`${colorize(FREE_GLYPH, "free")} ${freeSpace.label}: ${formatTokenCount(freeSpace.tokens)} tokens${percentText}`)
	}

	// Only reserveTokens is visualized as unavailable capacity.
	// keepRecentTokens is a compaction retention setting, not blocked space.
	if (typeof snapshot.compaction.reserveTokens === "number") {
		sidebarLines.push(`${colorize(RESERVED_GLYPH, "reserved")} Reserve tokens: ${formatTokenCount(snapshot.compaction.reserveTokens)} tokens`)
	}

	sidebarLines.push("")
	sidebarLines.push(`${bold("Session")}: ${snapshot.sessionId ?? "?"}`)
	if (snapshot.sessionFile) sidebarLines.push(`${bold("File")}: ${basename(snapshot.sessionFile)}`)

	if (width >= 90 && usageGrid.length > 0) {
		const leftWidth = Math.max(...usageGrid.map(visibleWidth)) + 2
		const gap = "   "
		const rightWidth = Math.max(24, width - leftWidth - gap.length)
		const rowCount = Math.max(usageGrid.length, sidebarLines.length)

		for (let rowIndex = 0; rowIndex < rowCount; rowIndex++) {
			const left = rowIndex < usageGrid.length ? `  ${usageGrid[rowIndex]}` : ""
			const right = rowIndex < sidebarLines.length ? clampLineToWidth(sidebarLines[rowIndex] ?? "", rightWidth) : ""
			lines.push(clamp(`${padVisibleEnd(left, leftWidth)}${gap}${right}`))
		}
	} else {
		for (const row of usageGrid) lines.push(clamp(`  ${row}`))
		for (const line of sidebarLines) lines.push(clamp(line))
	}

	lines.push("")
	return lines
}

function renderActionButtons(width: number): string {
	return clampLineToWidth(
		[
			colorize(" [b] Open HTML in browser ", "system-prompt"),
			colorize(" [e] Export JSON ", "free"),
			colorize(" [q] Close ", "reserved"),
		].join("  "),
		width,
	)
}

function renderSections(snapshot: ContextSnapshot, state: InspectorState, width: number): string[] {
	const clamp = (s: string) => clampLineToWidth(s, width)
	const lines = renderUsageHeader(snapshot, width)

	lines.push(renderActionButtons(width))
	lines.push(clamp(bold("Use ↑↓ to move, Enter/→ to open, b for browser, e to export, q/Esc to close")))
	lines.push("")

	for (let i = 0; i < snapshot.sections.length; i++) {
		const section = snapshot.sections[i]!
		const marker = i === state.selectedSection ? "➜" : " "
		lines.push(clamp(`${marker} ${section.title} [${section.items.length}] — ${section.summary}`))
	}

	return lines
}

function renderItems(snapshot: ContextSnapshot, state: InspectorState, width: number): string[] {
	const section = sectionAt(snapshot, state)
	const clamp = (s: string) => clampLineToWidth(s, width)
	const lines = renderUsageHeader(snapshot, width)

	if (!section) {
		lines.push(clamp("No section selected"))
		return lines
	}

	lines.push(clamp(`${section.title} • ${formatSectionSummary(section)}`))
	lines.push(renderActionButtons(width))
	lines.push(clamp("Use ↑↓ to move, Enter/→/o/Space to view full item, ← to sections, b for browser, e to export, q/Esc to close"))
	lines.push("")

	if (section.items.length === 0) {
		lines.push(clamp("(no items)"))
		return lines
	}

	const windowSize = 10
	const start = Math.max(0, Math.min(state.selectedItem - Math.floor(windowSize / 2), Math.max(0, section.items.length - windowSize)))
	const end = Math.min(section.items.length, start + windowSize)

	if (start > 0) lines.push(clamp("…"))

	for (let i = start; i < end; i++) {
		const item = section.items[i]!
		const selected = i === state.selectedItem ? "➜" : " "
		lines.push(clamp(`${selected} ${item.title} [${item.sourceType}] ~${item.tokenEstimate} tok`))
		lines.push(clamp(`  ${item.preview}`))
	}

	if (end < section.items.length) lines.push(clamp("…"))

	return lines
}


function horizontalRule(width: number, left = "├", fill = "─", right = "┤"): string {
	return `${left}${fill.repeat(Math.max(0, width - 2))}${right}`
}

function boxedLine(text: string, width: number): string {
	const innerWidth = Math.max(0, width - 4)
	const content = padVisibleEnd(truncateToWidth(text, innerWidth, ""), innerWidth)
	return `│ ${content} │`
}

function renderDetailHeader(section: SnapshotSection, item: SnapshotItem, width: number): string[] {
	const headerWidth = Math.max(24, width)
	return [
		horizontalRule(headerWidth, "╭", "─", "╮"),
		boxedLine(`Item detail: ${section.title}`, headerWidth),
		boxedLine(`Selected: ${item.title}`, headerWidth),
		boxedLine(`Source: ${item.sourceType}${item.sourceId ? ` / ${item.sourceId}` : ""}`, headerWidth),
		boxedLine(`Estimated tokens: ~${item.tokenEstimate}`, headerWidth),
		horizontalRule(headerWidth, "╰", "─", "╯"),
	]
}

function styleDetailBodyLine(line: string, width: number): string[] {
	const clean = sanitizeForTerminal(line)
	const trimmed = clean.trim()

	if (!trimmed) return [""]

	// Markdown heading support: #, ##, ###, etc.
	const heading = trimmed.match(/^(#{1,6})\s+(.+)$/)
	if (heading) {
		const level = heading[1]?.length ?? 1
		const title = heading[2] ?? ""
		const prefix = level <= 2 ? "▰" : "▸"
		return [
			"",
			truncateToWidth(colorize(`${prefix} ${title}`, "system-prompt"), width, ""),
			truncateToWidth(colorize("─".repeat(Math.min(width, Math.max(12, title.length + 2))), "system-prompt"), width, ""),
		]
	}

	// Common prompt section headings, for prompts that are not strictly Markdown.
	if (/^[A-Z][A-Za-z0-9 /&()_-]{2,}:$/.test(trimmed) || /^<{2,3}[^>]+>{2,3}$/.test(trimmed)) {
		return [
			"",
			truncateToWidth(colorize(`▸ ${trimmed}`, "system-prompt"), width, ""),
		]
	}

	// Horizontal separators.
	if (/^[-=_]{3,}$/.test(trimmed)) {
		return [colorize("─".repeat(Math.min(width, 72)), "free")]
	}

	// Markdown bullets.
	const bullet = clean.match(/^(\s*)[-*+]\s+(.+)$/)
	if (bullet) {
		const indent = bullet[1] ?? ""
		const body = bullet[2] ?? ""
		return wrapInspectorLine(`${indent}• ${body}`, width)
	}

	// Numbered lists.
	const numbered = clean.match(/^(\s*)(\d+)[.)]\s+(.+)$/)
	if (numbered) {
		const indent = numbered[1] ?? ""
		const number = numbered[2] ?? ""
		const body = numbered[3] ?? ""
		return wrapInspectorLine(`${indent}${number}. ${body}`, width)
	}

	// Tool/function-like lines are common in generated system prompts.
	if (/^\s*[-•]?\s*[a-zA-Z0-9_.-]+:\s+/.test(clean)) {
		return wrapInspectorLine(clean, width).map((wrapped) => colorize(wrapped, "skills"))
	}

	return wrapInspectorLine(clean, width)
}

function formatDetailBody(body: string, width: number): string[] {
	return body.split("\n").flatMap((line) => styleDetailBodyLine(line, width))
}

function renderDetail(snapshot: ContextSnapshot, state: InspectorState, width: number): string[] {
	const section = sectionAt(snapshot, state)
	const item = itemAt(snapshot, state)
	const clamp = (s: string) => clampLineToWidth(s, width)
	const lines = renderUsageHeader(snapshot, width)

	if (!section || !item) {
		lines.push(clamp("No item selected"))
		return lines
	}

	lines.push(...renderDetailHeader(section, item, width))
	lines.push(renderActionButtons(width))
	lines.push(clamp("DETAIL VIEW — Use ↑↓ to scroll, ← to item list, b for browser, e to export, q/Esc to close"))
	lines.push(colorize(horizontalRule(width, "╞", "═", "╡"), "free"))

	const bodyWidth = Math.max(20, width - 4)
	const bodyLines = formatDetailBody(item.body, bodyWidth)

	const maxBodyLines = 22
	const maxScroll = Math.max(0, bodyLines.length - maxBodyLines)
	const scroll = Math.max(0, Math.min(state.detailScroll, maxScroll))
	const visibleBody = bodyLines.slice(scroll, scroll + maxBodyLines)

	if (scroll > 0) {
		lines.push(clamp(colorize(`… ${scroll} formatted line(s) above`, "free")))
	}

	for (const line of visibleBody) {
		if (!line) {
			lines.push("")
			continue
		}
		lines.push(clamp(`  ${line}`))
	}

	if (scroll + maxBodyLines < bodyLines.length) {
		lines.push(clamp(colorize(`… ${bodyLines.length - scroll - maxBodyLines} formatted line(s) below`, "free")))
	}

	return lines
}
function buildInspectorLines(snapshot: ContextSnapshot, state: InspectorState, width: number): string[] {
	switch (state.view) {
		case "sections":
			return renderSections(snapshot, state, width)
		case "items":
			return renderItems(snapshot, state, width)
		case "detail":
			return renderDetail(snapshot, state, width)
	}
}

function styleInspectorLines(lines: string[], width: number): string[] {
	const contentWidth = Math.max(20, width - 4)
	const borderColor = "\x1b[38;5;244m"
	const panelBg = "\x1b[48;5;236m"
	const textColor = "\x1b[38;5;255m"
	const reset = "\x1b[0m"
	const border = `${borderColor}│${reset}`
	const top = `${borderColor}╭${"─".repeat(contentWidth + 2)}╮${reset}`
	const bottom = `${borderColor}╰${"─".repeat(contentWidth + 2)}╯${reset}`

	const panelStyle = `${panelBg}${textColor}`
	const body = lines.map((line) => {
		// Some lines contain ANSI color codes for the usage grid/legend.
		// Padding with String.length misplaces the right border because escape
		// sequences are counted as characters even though they have no width.
		const truncated = truncateToWidth(String(line ?? ""), contentWidth, "")
		const content = padVisibleEnd(truncated, contentWidth)

		// Inner color helpers use full SGR resets (\x1b[0m). Re-apply the panel
		// style after those resets, otherwise the overlay becomes half opaque and
		// half transparent wherever colored glyphs/actions are rendered.
		const styledContent = content.replace(/\x1b\[0m/g, `${reset}${panelStyle}`)

		return `${border}${panelStyle} ${styledContent} ${reset}${border}`
	})

	return [top, ...body, bottom]
}

function resetRenderCache(cache: { width: number; stateKey: string; lines: string[] }) {
	cache.width = 0
	cache.stateKey = ""
	cache.lines = []
}

function inspectorStateKey(state: InspectorState): string {
	return `${state.view}:${state.selectedSection}:${state.selectedItem}:${state.detailScroll}`
}

function clampSelection(state: InspectorState, snapshot: ContextSnapshot) {
	state.selectedSection = Math.max(0, Math.min(state.selectedSection, snapshot.sections.length - 1))
	const section = sectionAt(snapshot, state)
	state.selectedItem = Math.max(0, Math.min(state.selectedItem, Math.max(0, (section?.items.length ?? 1) - 1)))
	state.detailScroll = Math.max(0, state.detailScroll)
}

function resolveProjectPath(cwd: string, userPath: string): string {
	const resolved = resolve(cwd, userPath)
	const rel = relative(cwd, resolved)

	if (rel === "" || rel === ".." || rel.startsWith(`..${"/"}`) || rel.startsWith(`..${"\\"}`) || resolve(rel) === rel) {
		throw new Error("Export path must stay inside the project")
	}

	return resolved
}

function sanitizeFilenameSegment(value: string): string {
	const sanitized = value.replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "")
	return sanitized.slice(0, 96) || "ephemeral"
}

function defaultSnapshotPath(snapshot: ContextSnapshot, extension: "html" | "json"): string {
	const session = sanitizeFilenameSegment(snapshot.sessionId ?? "ephemeral")
	return join(tmpdir(), DEFAULT_EXPORT_DIR, `context-snapshot-${session}.local.${extension}`)
}

async function chmodBestEffort(path: string, mode: number): Promise<void> {
	try {
		await chmod(path, mode)
	} catch {
		// Some filesystems/platforms do not support POSIX chmod. The temp dir
		// location still keeps these local-only; use best-effort permissions.
	}
}

async function writePrivateTextFile(outputPath: string, content: string): Promise<void> {
	const outputDir = dirname(outputPath)
	await mkdir(outputDir, { recursive: true, mode: 0o700 })
	await chmodBestEffort(outputDir, 0o700)
	await writeFile(outputPath, content, { encoding: "utf8", mode: 0o600 })
	await chmodBestEffort(outputPath, 0o600)
}

function escapeHtml(value: unknown): string {
	const replacements: Record<string, string> = {
		"&": "&amp;",
		"<": "&lt;",
		">": "&gt;",
		'"': "&quot;",
		"'": "&#39;",
	}

	return String(value ?? "").replace(/[&<>"']/g, (char) => replacements[char] ?? char)
}

function htmlId(value: string): string {
	const normalized = value.toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "")
	return normalized || "item"
}

function formatPercent(percent: number | undefined): string {
	if (typeof percent !== "number" || !Number.isFinite(percent)) return "n/a"
	return `${percent.toFixed(1)}%`
}

function usageCellGlyph(category: UsageCategory): string {
	if (category.id === "free") return FREE_GLYPH
	if (category.id === "reserved") return RESERVED_GLYPH
	return USED_GLYPH
}

function allocateUsageGridCategories(categories: UsageCategory[]): UsageCategory[] {
	if (categories.length === 0) return []

	const totalCells = 100
	const exactCells = categories.map((category) => {
		const exact = typeof category.percentOfWindow === "number" ? (category.percentOfWindow / 100) * totalCells : 0
		return { category, exact, cells: Math.floor(exact), remainder: exact - Math.floor(exact) }
	})

	let assigned = exactCells.reduce((sum: number, entry: { cells: number }) => sum + entry.cells, 0)
	for (const entry of [...exactCells].sort((a, b) => b.remainder - a.remainder)) {
		if (assigned >= totalCells) break
		entry.cells += 1
		assigned += 1
	}

	const cells = exactCells.flatMap((entry) => Array<UsageCategory>(entry.cells).fill(entry.category)).slice(0, totalCells)
	while (cells.length < totalCells) {
		cells.push({ id: "free", label: "Free space", symbol: FREE_GLYPH, tokens: 0 })
	}

	return cells
}

function renderHtmlUsageGrid(categories: UsageCategory[]): string {
	const cells = allocateUsageGridCategories(categories)
	if (cells.length === 0) return `<div class="usage-grid empty">No usage data available</div>`

	return `<div class="usage-grid" aria-label="Estimated context window usage grid">${cells
		.map((category) => {
			const className = `cat-${htmlId(category.id)}`
			const title = `${category.label}: ${formatTokenCount(category.tokens)} tokens (${formatPercent(category.percentOfWindow)})`
			return `<span class="usage-cell ${className}" title="${escapeHtml(title)}" aria-label="${escapeHtml(title)}">${escapeHtml(usageCellGlyph(category))}</span>`
		})
		.join("")}</div>`
}

function renderHtmlCategoryLegend(categories: UsageCategory[]): string {
	if (categories.length === 0) return `<p class="muted">No usage categories available.</p>`

	return `<div class="legend-grid">${categories
		.map((category) => {
			const className = `cat-${htmlId(category.id)}`
			return `
				<div class="legend-row">
					<span class="legend-swatch ${className}">${escapeHtml(usageCellGlyph(category))}</span>
					<span class="legend-label">${escapeHtml(category.label)}</span>
					<span class="legend-tokens">${escapeHtml(formatTokenCount(category.tokens))} tokens</span>
					<span class="legend-percent">${escapeHtml(formatPercent(category.percentOfWindow))}</span>
				</div>`
		})
		.join("")}</div>`
}

function renderHtmlItem(section: SnapshotSection, item: SnapshotItem): string {
	const itemId = `${htmlId(section.id)}-${htmlId(item.id)}`
	const meta = item.meta
		? `<div class="item-meta"><h4>Metadata</h4><pre>${escapeHtml(safeJson(item.meta))}</pre></div>`
		: ""

	return `
		<details class="item-card" id="${itemId}">
			<summary>
				<span class="item-title">${escapeHtml(item.title)}</span>
				<span class="item-kind">${escapeHtml(item.sourceType)}</span>
				<span class="item-tokens">~${escapeHtml(formatTokenCount(item.tokenEstimate))} tokens</span>
			</summary>
			<p class="item-preview">${escapeHtml(item.preview)}</p>
			<pre class="item-body">${escapeHtml(item.body)}</pre>
			${meta}
		</details>`
}

function renderHtmlSection(section: SnapshotSection): string {
	const sectionId = `section-${htmlId(section.id)}`
	const items = section.items.length > 0
		? section.items.map((item) => renderHtmlItem(section, item)).join("\n")
		: `<p class="muted">No items in this section.</p>`

	return `
		<section class="section-card" id="${sectionId}">
			<div class="section-heading">
				<div>
					<p class="eyebrow">${escapeHtml(section.id)}</p>
					<h2>${escapeHtml(section.title)}</h2>
				</div>
				<div class="section-stats">
					<span>${section.items.length} item${section.items.length === 1 ? "" : "s"}</span>
					<span>~${escapeHtml(formatTokenCount(section.tokenEstimate))} tokens</span>
				</div>
			</div>
			<p class="section-summary">${escapeHtml(section.summary)}</p>
			<div class="items">${items}</div>
		</section>`
}

function renderSnapshotHtml(snapshot: ContextSnapshot): string {
	const rawUsageTokens = typeof snapshot.usage?.tokens === "number" ? snapshot.usage.tokens : null
	const usageWindow = typeof snapshot.usage?.contextWindow === "number" ? snapshot.usage.contextWindow : null
	const estimatedUsedTokens = snapshot.usageCategories
		.filter((category: UsageCategory) => category.id !== "free" && category.id !== "reserved")
		.reduce((sum: number, category: UsageCategory) => sum + category.tokens, 0)
	const usageTokens = Math.max(rawUsageTokens ?? 0, estimatedUsedTokens)
	const usagePercent = usageWindow ? (usageTokens / usageWindow) * 100 : undefined
	const rawSnapshot = { warning: SNAPSHOT_WARNING, ...snapshot }

	const navLinks = snapshot.sections
		.map((section) => `<a href="#section-${htmlId(section.id)}">${escapeHtml(section.title)}</a>`)
		.join("\n")

	return `<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<title>Pi Context Snapshot${snapshot.sessionId ? ` — ${escapeHtml(snapshot.sessionId)}` : ""}</title>
	<style>
		:root {
			color-scheme: dark;
			--bg: #080910;
			--panel: #11131d;
			--panel-2: #171a27;
			--border: #2b3042;
			--text: #f3f5ff;
			--muted: #9ca3b7;
			--dim: #6f778f;
			--accent: #e20074;
			--accent-2: #6ee7ff;
			--success: #60d394;
			--warning: #fbbf24;
			--error: #fb7185;
			--shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
		}

		* { box-sizing: border-box; }
		body {
			margin: 0;
			font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
			background:
				radial-gradient(circle at top left, rgba(226, 0, 116, 0.22), transparent 32rem),
				radial-gradient(circle at top right, rgba(110, 231, 255, 0.12), transparent 28rem),
				var(--bg);
			color: var(--text);
			line-height: 1.55;
		}

		a { color: inherit; text-decoration: none; }
		button {
			border: 1px solid rgba(226, 0, 116, 0.55);
			border-radius: 999px;
			background: rgba(226, 0, 116, 0.13);
			color: var(--text);
			padding: 0.55rem 0.85rem;
			cursor: pointer;
		}
		button:hover { background: rgba(226, 0, 116, 0.25); }

		.hero {
			padding: 2.5rem clamp(1rem, 4vw, 4rem) 1.5rem;
			border-bottom: 1px solid var(--border);
		}
		.hero h1 { margin: 0; font-size: clamp(2rem, 5vw, 4rem); letter-spacing: -0.06em; }
		.hero p { color: var(--muted); max-width: 78rem; }
		.warning {
			border: 1px solid rgba(251, 191, 36, 0.45);
			background: rgba(251, 191, 36, 0.1);
			color: #fde68a;
			border-radius: 1rem;
			padding: 0.9rem 1rem;
			margin-top: 1rem;
		}

		.layout {
			display: grid;
			grid-template-columns: minmax(14rem, 18rem) minmax(0, 1fr);
			gap: 1.25rem;
			padding: 1.25rem clamp(1rem, 4vw, 4rem) 4rem;
		}
		.sidebar {
			position: sticky;
			top: 1rem;
			align-self: start;
			border: 1px solid var(--border);
			background: rgba(17, 19, 29, 0.86);
			backdrop-filter: blur(18px);
			border-radius: 1.25rem;
			padding: 1rem;
			box-shadow: var(--shadow);
		}
		.sidebar h2 { font-size: 0.82rem; text-transform: uppercase; color: var(--dim); letter-spacing: 0.14em; }
		.sidebar nav { display: grid; gap: 0.35rem; margin: 0.8rem 0 1rem; }
		.sidebar a { color: var(--muted); border-radius: 0.7rem; padding: 0.45rem 0.55rem; }
		.sidebar a:hover { color: var(--text); background: rgba(255, 255, 255, 0.06); }
		.actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }

		main { display: grid; gap: 1.25rem; min-width: 0; }
		.panel, .section-card {
			border: 1px solid var(--border);
			background: linear-gradient(180deg, rgba(23, 26, 39, 0.96), rgba(17, 19, 29, 0.96));
			border-radius: 1.35rem;
			padding: clamp(1rem, 2.5vw, 1.6rem);
			box-shadow: var(--shadow);
		}
		.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr)); gap: 0.8rem; margin: 1rem 0; }
		.stat { border: 1px solid var(--border); border-radius: 1rem; padding: 0.9rem; background: rgba(255, 255, 255, 0.035); }
		.stat-label { display: block; color: var(--dim); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.12em; }
		.stat-value { display: block; margin-top: 0.25rem; font-size: 1.15rem; font-weight: 700; overflow-wrap: anywhere; }
		.usage-bar { height: 0.8rem; border-radius: 999px; overflow: hidden; background: rgba(255, 255, 255, 0.08); border: 1px solid var(--border); }
		.usage-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-2)); width: ${Math.max(0, Math.min(100, usagePercent ?? 0)).toFixed(2)}%; }
		.usage-layout { display: grid; grid-template-columns: minmax(13rem, 18rem) minmax(0, 1fr); gap: 1rem; align-items: start; margin-top: 1rem; }
		.usage-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 0.35rem; }
		.usage-grid.empty { display: block; color: var(--muted); }
		.usage-cell, .legend-swatch { display: inline-grid; place-items: center; border-radius: 0.45rem; min-width: 1.45rem; min-height: 1.45rem; font-size: 0.8rem; color: #05060a; font-weight: 800; }
		.legend-grid { display: grid; gap: 0.45rem; }
		.legend-row { display: grid; grid-template-columns: 2rem minmax(0, 1fr) auto auto; gap: 0.75rem; align-items: center; color: var(--muted); }
		.legend-label { color: var(--text); }
		.legend-tokens, .legend-percent { font-variant-numeric: tabular-nums; white-space: nowrap; }

		.cat-system-prompt { background: #22d3ee; }
		.cat-base-system-prompt { background: #38bdf8; }
		.cat-system-tools { background: #86efac; }
		.cat-mcp-tools { background: #f0abfc; }
		.cat-memory-files { background: #bae6fd; }
		.cat-skills { background: #fde047; }
		.cat-messages { background: #f8fafc; }
		.cat-other { background: #fb7185; }
		.cat-free { background: #475569; color: #dbe4ef; }
		.cat-reserved { background: #71717a; color: #f4f4f5; }

		.section-heading { display: flex; justify-content: space-between; gap: 1rem; align-items: start; }
		.eyebrow { margin: 0 0 0.2rem; color: var(--accent-2); text-transform: uppercase; letter-spacing: 0.14em; font-size: 0.75rem; }
		h2 { margin: 0; font-size: clamp(1.25rem, 2vw, 1.8rem); }
		.section-stats { display: flex; gap: 0.5rem; flex-wrap: wrap; justify-content: flex-end; }
		.section-stats span, .item-kind, .item-tokens {
			border: 1px solid var(--border);
			border-radius: 999px;
			padding: 0.2rem 0.55rem;
			color: var(--muted);
			font-size: 0.78rem;
			white-space: nowrap;
		}
		.section-summary, .muted { color: var(--muted); }
		.items { display: grid; gap: 0.65rem; margin-top: 1rem; }
		.item-card { border: 1px solid var(--border); border-radius: 1rem; background: rgba(255, 255, 255, 0.035); overflow: hidden; }
		.item-card[open] { background: rgba(226, 0, 116, 0.06); }
		.item-card summary {
			display: flex;
			gap: 0.55rem;
			align-items: center;
			padding: 0.8rem 0.9rem;
			cursor: pointer;
		}
		.item-title { font-weight: 700; flex: 1; overflow-wrap: anywhere; }
		.item-preview { margin: 0; padding: 0 0.9rem 0.85rem; color: var(--muted); }
		pre {
			white-space: pre-wrap;
			word-break: break-word;
			background: #070812;
			border-top: 1px solid var(--border);
			border-bottom: 1px solid var(--border);
			margin: 0;
			padding: 1rem;
			max-height: 42rem;
			overflow: auto;
			font-size: 0.88rem;
			line-height: 1.5;
		}
		.item-meta h4 { margin: 0; padding: 0.85rem 1rem 0.35rem; color: var(--muted); }
		.raw details summary { cursor: pointer; font-weight: 700; }
		.footer-note { color: var(--dim); font-size: 0.85rem; }

		@media (max-width: 880px) {
			.layout { grid-template-columns: 1fr; }
			.sidebar { position: static; }
			.usage-layout { grid-template-columns: 1fr; }
			.legend-row { grid-template-columns: 2rem minmax(0, 1fr); }
			.legend-tokens, .legend-percent { grid-column: 2; }
			.section-heading { display: grid; }
			.section-stats { justify-content: flex-start; }
		}
	</style>
</head>
<body>
	<header class="hero">
		<h1>Pi Context Snapshot</h1>
		<p>Generated ${escapeHtml(snapshot.generatedAt)} for <strong>${escapeHtml(snapshot.model ?? "no-model")}</strong>. This is a local HTML rendering of the same read-only snapshot shown by <code>/context</code>.</p>
		<div class="warning">${escapeHtml(SNAPSHOT_WARNING)}</div>
	</header>

	<div class="layout">
		<aside class="sidebar">
			<h2>Snapshot</h2>
			<nav>${navLinks}</nav>
			<div class="actions">
				<button type="button" data-action="expand">Expand all</button>
				<button type="button" data-action="collapse">Collapse all</button>
			</div>
			<p class="footer-note">File: ${escapeHtml(snapshot.sessionFile ? basename(snapshot.sessionFile) : "ephemeral session")}</p>
		</aside>

		<main>
			<section class="panel" id="overview">
				<p class="eyebrow">Overview</p>
				<h2>Session at a glance</h2>
				<div class="stat-grid">
					<div class="stat"><span class="stat-label">Session</span><span class="stat-value">${escapeHtml(snapshot.sessionId ?? "?")}</span></div>
					<div class="stat"><span class="stat-label">Model</span><span class="stat-value">${escapeHtml(snapshot.model ?? "no-model")}</span></div>
					<div class="stat"><span class="stat-label">Thinking</span><span class="stat-value">${escapeHtml(snapshot.thinkingLevel ?? "?")}</span></div>
					<div class="stat"><span class="stat-label">Context</span><span class="stat-value">${escapeHtml(formatTokenCount(usageTokens))} / ${escapeHtml(formatTokenCount(usageWindow))}</span></div>
					<div class="stat"><span class="stat-label">Working directory</span><span class="stat-value">${escapeHtml(snapshot.cwd)}</span></div>
				</div>
				<div class="usage-bar" aria-label="Context usage"><div class="usage-fill"></div></div>
				<div class="usage-layout">
					${renderHtmlUsageGrid(snapshot.usageCategories)}
					${renderHtmlCategoryLegend(snapshot.usageCategories)}
				</div>
			</section>

			${snapshot.sections.map(renderHtmlSection).join("\n")}

			<section class="panel raw" id="raw-snapshot">
				<details>
					<summary>Raw snapshot JSON</summary>
					<pre>${escapeHtml(JSON.stringify(rawSnapshot, null, 2))}</pre>
				</details>
			</section>
		</main>
	</div>

	<script>
		const setAllDetails = (open) => document.querySelectorAll("details").forEach((detail) => { detail.open = open; });
		document.querySelector('[data-action="expand"]')?.addEventListener("click", () => setAllDetails(true));
		document.querySelector('[data-action="collapse"]')?.addEventListener("click", () => setAllDetails(false));
	</script>
</body>
</html>`
}

async function exportHtmlSnapshot(ctx: ExtensionCommandContext, snapshot: ContextSnapshot, rawPath?: string): Promise<string> {
	const outputPath = rawPath ? resolveProjectPath(ctx.cwd, rawPath) : defaultSnapshotPath(snapshot, "html")

	await writePrivateTextFile(outputPath, renderSnapshotHtml(snapshot))

	return outputPath
}

function browserOpenCommand(filePath: string): { command: string; args: string[] } {
	const url = pathToFileURL(filePath).href

	if (process.platform === "darwin") return { command: "open", args: [url] }
	if (process.platform === "win32") return { command: "cmd", args: ["/c", "start", "", url] }
	return { command: "xdg-open", args: [url] }
}

async function openFileInBrowser(filePath: string): Promise<void> {
	const { command, args } = browserOpenCommand(filePath)

	await new Promise<void>((resolvePromise, reject) => {
		const child = execFile(command, args, { timeout: 10000, windowsHide: true }, (error) => {
			if (error) reject(error)
			else resolvePromise()
		})
		child.stdin?.end()
	})
}

function formatError(error: unknown): string {
	return error instanceof Error ? error.message : String(error)
}

async function openHtmlSnapshot(ctx: ExtensionCommandContext, snapshot: ContextSnapshot, rawPath?: string) {
	const outputPath = await exportHtmlSnapshot(ctx, snapshot, rawPath)

	try {
		await openFileInBrowser(outputPath)
		ctx.ui.notify(`Opened context HTML in browser: ${outputPath}`, "info")
	} catch (error) {
		ctx.ui.notify(`Wrote HTML to ${outputPath}, but could not open browser: ${formatError(error)}`, "warning")
	}
}

async function exportSnapshot(ctx: ExtensionCommandContext, snapshot: ContextSnapshot, rawPath?: string) {
	const outputPath = rawPath ? resolveProjectPath(ctx.cwd, rawPath) : defaultSnapshotPath(snapshot, "json")

	await writePrivateTextFile(
		outputPath,
		JSON.stringify(
			{
				warning: SNAPSHOT_WARNING,
				...snapshot,
			},
			null,
			2,
		),
	)

	ctx.ui.notify(`Exported snapshot to ${outputPath}`, "info")
}

function isCloseKey(data: string): boolean {
	return matchesKey(data, Key.escape) || data === "q" || data === "Q"
}

function isOpenKey(data: string): boolean {
	// Different terminal/TUI layers may send Enter as a named key, CR, LF,
	// or CRLF. Support all common forms so opening item detail is reliable.
	return (
		matchesKey(data, Key.enter) ||
		matchesKey(data, Key.right) ||
		data === "\r" ||
		data === "\n" ||
		data === "\r\n" ||
		data === "o" ||
		data === "O" ||
		data === " "
	)
}

/**
 * Update navigation state in response to one keypress.
 *
 * This function intentionally contains only navigation behavior. Rendering and
 * exporting stay outside so the UI loop remains easy to reason about.
 */
function handleNavigationInput(state: InspectorState, snapshot: ContextSnapshot, data: string): boolean {
	const section = sectionAt(snapshot, state)
	const itemCount = section?.items.length ?? 0

	if (isOpenKey(data)) {
		if (state.view === "sections") {
			state.selectedItem = 0
			state.detailScroll = 0

			// If a section has only one item, skip the intermediate list.
			// This makes sections like "System prompt & resources" open
			// directly into the full prompt detail view.
			state.view = itemCount === 1 ? "detail" : "items"
			return true
		}

		if (state.view === "items" && itemCount > 0) {
			state.view = "detail"
			state.detailScroll = 0
			return true
		}

		return false
	}

	if (matchesKey(data, Key.left)) {
		if (state.view === "detail") {
			state.view = "items"
			state.detailScroll = 0
			return true
		}

		if (state.view === "items") {
			state.view = "sections"
			state.detailScroll = 0
			return true
		}

		return false
	}

	if (matchesKey(data, Key.up)) {
		if (state.view === "sections") {
			state.selectedSection = Math.max(0, state.selectedSection - 1)
			state.selectedItem = 0
			state.detailScroll = 0
			return true
		}

		if (state.view === "items") {
			state.selectedItem = Math.max(0, state.selectedItem - 1)
			state.detailScroll = 0
			return true
		}

		if (state.view === "detail") {
			state.detailScroll = Math.max(0, state.detailScroll - 1)
			return true
		}
	}

	if (matchesKey(data, Key.down)) {
		if (state.view === "sections") {
			state.selectedSection = Math.min(snapshot.sections.length - 1, state.selectedSection + 1)
			state.selectedItem = 0
			state.detailScroll = 0
			return true
		}

		if (state.view === "items") {
			state.selectedItem = Math.min(Math.max(0, itemCount - 1), state.selectedItem + 1)
			state.detailScroll = 0
			return true
		}

		if (state.view === "detail") {
			state.detailScroll += 1
			return true
		}
	}

	return false
}

async function openInspector(ctx: ExtensionCommandContext, pi: ExtensionAPI, cache: PromptCache | undefined) {
	const snapshot = buildSnapshot(ctx, pi, cache)
	const state: InspectorState = {
		view: "sections",
		selectedSection: 0,
		selectedItem: 0,
		detailScroll: 0,
	}

	let doneFn: ((value: void) => void) | undefined
	const renderCache = { width: 0, stateKey: "", lines: [] as string[] }

	await ctx.ui.custom<void>(
		(tui, _theme, _kb, done) => {
			doneFn = done

			return {
				render: (width: number) => {
					clampSelection(state, snapshot)

					const stateKey = inspectorStateKey(state)

					if (width !== renderCache.width || stateKey !== renderCache.stateKey) {
						renderCache.width = width
						renderCache.stateKey = stateKey
						renderCache.lines = styleInspectorLines(
							buildInspectorLines(snapshot, state, Math.max(20, width - 4)),
							width,
						)
					}

					return renderCache.lines
				},

				invalidate: () => {
					resetRenderCache(renderCache)
				},

				handleInput: (data: string) => {
					if (isCloseKey(data)) {
						doneFn?.(undefined)
						return
					}

					if (data === "b" || data === "B" || data === "h" || data === "H") {
						void openHtmlSnapshot(ctx, snapshot).catch((error) => {
							ctx.ui.notify(`Browser export failed: ${formatError(error)}`, "error")
						})
						return
					}

					if (data === "e" || data === "E") {
						void exportSnapshot(ctx, snapshot).catch((error) => {
							ctx.ui.notify(`Export failed: ${formatError(error)}`, "error")
						})
						return
					}

					const changed = handleNavigationInput(state, snapshot, data)
					if (changed) {
						resetRenderCache(renderCache)
						tui.requestRender()
					}
				},
			}
		},
		{
			overlay: true,
			overlayOptions: {
				width: "92%",
				maxHeight: "90%",
				anchor: "center",
			},
		},
	)
}

function parseCommandArgs(args: string | undefined): { command?: string; rest: string[] } {
	const trimmed = (args ?? "").trim()
	if (!trimmed) return { rest: [] }

	const [command, ...rest] = trimmed.split(/\s+/)
	return { command, rest }
}

export default function (pi: ExtensionAPI) {
	let latestPrompt: PromptCache | undefined

	pi.on("session_start", () => {
		latestPrompt = undefined
	})

	pi.on("session_shutdown", () => {
		latestPrompt = undefined
	})

	pi.on("before_agent_start", (event, ctx) => {
		latestPrompt = {
			systemPrompt: event.systemPrompt,
			options: clonePromptOptions(event.systemPromptOptions, ctx.cwd),
		}
	})

	pi.registerCommand("context", {
		description: "Inspect the current Pi context snapshot; press b to open an HTML browser view",

		handler: async (args: string | undefined, ctx: ExtensionCommandContext) => {
			const parsed = parseCommandArgs(args)

			if (parsed.command === "export") {
				if (!ctx.hasUI) {
					ctx.ui.notify("Context export needs an interactive session", "warning")
					return
				}

				if (!ctx.isIdle()) {
					ctx.ui.notify("Wait for the current turn to finish before exporting context", "warning")
					return
				}

				const snapshot = buildSnapshot(ctx, pi, latestPrompt)
				await exportSnapshot(ctx, snapshot, parsed.rest[0])
				return
			}

			if (parsed.command === "html" || parsed.command === "browser" || parsed.command === "open") {
				if (!ctx.isIdle()) {
					ctx.ui.notify("Wait for the current turn to finish before opening context HTML", "warning")
					return
				}

				const snapshot = buildSnapshot(ctx, pi, latestPrompt)
				await openHtmlSnapshot(ctx, snapshot, parsed.rest[0])
				return
			}

			if (parsed.command) {
				ctx.ui.notify(`Unknown /context command: ${parsed.command}`, "warning")
				return
			}

			if (!ctx.hasUI) {
				ctx.ui.notify("Context inspector needs an interactive session", "warning")
				return
			}

			if (!ctx.isIdle()) {
				ctx.ui.notify("Run /context after the current turn finishes", "warning")
				return
			}

			await openInspector(ctx, pi, latestPrompt)
		},
	})
}
