# OpenCode Agents

Available subagents and delegation guidance.

## Available Subagents

- `commit` — Git commit agent (pre-approved git commands)
- `explore` — Fast local codebase search, returns file paths + line numbers
- `manager` — Project manager using Linear MCP with BMAD-style workflows
- `librarian` — Research source code: GitHub repos, issues/PRs, library internals via `gh` CLI
- `web-researcher` — Web search: DuckDuckGo + webfetch for docs, tutorials, best practices
- `crawl` — Persist web content to ai-docs/ files (invoke via `/crawl` command or `@crawl`)

### Manager Agent (Max)

Specialized project manager agent using Linear MCP. Delegate to `@manager` when:

- Creating/updating issues, epics, or tasks in Linear
- Querying project or cycle status
- Breaking down work into stories with acceptance criteria

Manager uses BMAD-style workflows and menu triggers (e.g., `[RW]` for research, `[CE]` for epic). See `agent/manager.md` for full workflow documentation.

### Linear MCP Access

**All agents have access to Linear MCP tools**, but Linear-related tasks should be delegated to the `@manager` agent because:

1. **Specialized workflows** — Manager has BMAD-style workflows optimized for issue creation, project tracking, and cycle management
2. **Consistent formatting** — Manager uses templates that ensure issues have proper structure, acceptance criteria, and labels
3. **Context awareness** — Manager understands project hierarchy (initiatives, epics, stories) and can properly scope work
4. **Reduced noise** — Centralizing Linear operations prevents fragmented issue creation across agents

**When to delegate to @manager:**

- Creating issues, epics, or tasks
- Updating issue status or priority
- Querying project/cycle status
- Any operation that modifies Linear state

**When other agents may use Linear directly:**

- Read-only queries for context (e.g., checking if an issue exists)
- Emergency situations where manager is unavailable

### When to Use Each Agent

| Agent             | Trigger                                                       | Tools                          | Output                          |
| ----------------- | ------------------------------------------------------------- | ------------------------------ | ------------------------------- |
| `@explore`        | "Where is X?", "Find files for Y"                             | Read-only local tools          | File paths + line numbers       |
| `@manager`        | "Create issue for X", "Project status?", `[RW]`, `[CE]`, etc. | Linear MCP tools               | Issue/project links + summaries |
| `@librarian`      | "How does [lib] implement X?", "GitHub issues for Y"          | `gh` CLI, git clone, webfetch  | Permalinks + code snippets      |
| `@web-researcher` | "Best practices for X", "Compare A vs B", "Find URLs about Y" | DuckDuckGo, webfetch, crawl4ai | URLs + synthesized findings     |
| `@crawl`          | "Save docs for X to ai-docs/", `/crawl <url>`                 | crawl4ai, write                | Persisted markdown files        |

**Note**: `@librarian` can delegate to `@web-researcher` when it needs to discover URLs about a topic before investigating them with `gh` CLI.

### crawl4ai Skill

All agents can use the `crawl4ai` skill for JavaScript-heavy sites or structured extraction. Load with:

```
skill({ name: "crawl4ai" })
```

## Request Classification

Before taking action on a user request, classify it to determine the appropriate approach:

| Type            | Signal                                        | Action                                           |
| --------------- | --------------------------------------------- | ------------------------------------------------ |
| **Trivial**     | Single file, known location, direct answer    | Direct tools only                                |
| **Explicit**    | Specific file/line, clear command             | Execute directly                                 |
| **Exploratory** | "How does X work?", "Find Y"                  | Fire `@explore` (1-3 agents) + tools in parallel |
| **Open-ended**  | "Improve", "Refactor", "Add feature"          | Assess codebase first, then plan                 |
| **External**    | Library questions, "how does [package] work?" | Delegate to `@librarian`                         |
| **Ambiguous**   | Unclear scope, multiple interpretations       | Ask ONE clarifying question                      |

### Agent Delegation Triggers

| Pattern                                     | Action                                   |
| ------------------------------------------- | ---------------------------------------- |
| 2+ modules/directories involved             | Fire `@explore` in background            |
| External library/API mentioned              | Fire `@librarian` in background          |
| "Where is X?" questions                     | Use `@explore` for fast search           |
