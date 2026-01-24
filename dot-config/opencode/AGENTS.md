# OpenCode Configuration

Custom commands, agents, and skills for OpenCode AI assistant.

## Structure

| Path                  | Purpose                              |
| --------------------- | ------------------------------------ |
| `opencode.jsonc`      | Main config (provider, MCP, permissions) |
| `command/*.md`        | Custom slash commands                |
| `agent/*.md`          | Custom subagents                     |
| `skill/*/SKILL.md`    | Skills with scripts and references   |

## Commands

| Command         | Purpose                    |
| --------------- | -------------------------- |
| `opencode`      | Start OpenCode             |
| `oc`            | Alias for opencode         |
| `bun install`   | Install dependencies       |

## Custom Commands

Create `command/<name>.md` with YAML frontmatter:

```markdown
---
description: Brief description shown in command list
model: provider/model-id
---

# Command Title

Instructions for the command in markdown...
```

**Current commands**:
- `research_codebase.md` — Document codebase through parallel research
- `create_plan.md` — Create detailed implementation plans

## Custom Agents

Create `agent/<name>.md` with YAML frontmatter (v1.1.1+ syntax):

```markdown
---
description: Brief description of what the agent does
mode: subagent
temperature: 0.5
# Disable non-permissionable tools you don't want
tools:
  write: false
  edit: false
  task: false
# Control permissionable tools via permission
permission:
  bash: allow
  skill: allow
  webfetch: deny
---

# Agent Name

Agent instructions in markdown...
```

**Current agents**:
- `commit.md` — Git commit agent (configured in opencode.jsonc)
- `explore.md` — Fast **local codebase** search, returns structured file locations (Haiku 4.5)
- `manager.md` — **Project manager** using Linear MCP. Tab-switchable primary agent (`mode: all`)
- `oracle.md` — Strategic advisor for architecture/debugging decisions (Opus 4.5)
- `librarian.md` — Research **source code**: GitHub repos, issues/PRs, library internals via `gh` CLI (GLM 4.7 Free)
- `web-researcher.md` — **Web search**: DuckDuckGo + webfetch for docs, tutorials, best practices. No GitHub access — use to discover URLs (GLM 4.7 Free)
- `web-crawler.md` — **Persist** web content to ai-docs/ files (Haiku 4.5)

### Agent Relationships

```
                    ┌─────────────────┐
                    │  Main Assistant │
                    └────────┬────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    │                        │                        │
    ▼                        ▼                        ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   @manager    │   │   @explore    │   │   @oracle     │
│ (Linear/PM)   │   │ (local code)  │   │ (strategy)    │
│ Tab-switch OK │   └───────────────┘   └───────────────┘
└───────┬───────┘
        │ can delegate for codebase context
        ▼
┌───────────────┐
│   @explore    │
└───────────────┘

        ┌───────────────┐
        │  @librarian   │
        │ (GitHub/code) │
        └───────┬───────┘
                │
                │ delegates for URL discovery
                ▼
       ┌───────────────┐
       │@web-researcher│
       │ (DuckDuckGo)  │
       └───────┬───────┘
               │
               │ can use for JS-heavy sites
               ▼
       ┌───────────────┐
       │ @web-crawler  │
       │ (persist to   │
       │  ai-docs/)    │
       └───────────────┘
```

### When to Use Each Agent

| Agent | Trigger | Tools | Output |
|-------|---------|-------|--------|
| `@explore` | "Where is X?", "Find files for Y" | Read-only local tools | File paths + line numbers |
| `@manager` | "Create issue for X", "Project status?" | Linear MCP tools | Issue/project links + summaries |
| `@librarian` | "How does [lib] implement X?", "GitHub issues for Y" | `gh` CLI, git clone, webfetch | Permalinks + code snippets |
| `@web-researcher` | "Best practices for X", "Compare A vs B", "Find URLs about Y" | DuckDuckGo, webfetch, crawl4ai | URLs + synthesized findings |
| `@web-crawler` | "Save docs for X to ai-docs/" | crawl4ai, write | Persisted markdown files |
| `@oracle` | Architecture decisions, 2+ failed attempts | Read-only, webfetch | Strategic recommendations |

### Librarian vs Web-Researcher

| Question Type | Use Agent | Why |
|---------------|-----------|-----|
| "How does React implement hooks?" | `@librarian` | Needs source code, GitHub permalinks |
| "Best practices for React hooks" | `@web-researcher` | Needs docs, articles, tutorials |
| "Why does [library] throw error X?" | `@librarian` | Search GitHub issues/PRs |
| "What does error X mean?" | `@web-researcher` | General explanation from docs |
| "Find examples of X in open source" | `@librarian` | Clone repos, search code |
| "Compare library A vs B" | `@web-researcher` | Articles, benchmarks, opinions |
| "Find documentation URLs for X" | `@web-researcher` | DuckDuckGo search for discovery |

**Note**: `@librarian` can delegate to `@web-researcher` when it needs to discover URLs about a topic before investigating them with `gh` CLI.

### crawl4ai Skill (Available to All Agents)

All agents can use the `crawl4ai` skill for JavaScript-heavy sites or structured extraction. Load with:
```
skill({ name: "crawl4ai" })
```

## Request Classification

Before taking action on a user request, classify it to determine the appropriate approach:

| Type | Signal | Action |
|------|--------|--------|
| **Trivial** | Single file, known location, direct answer | Direct tools only |
| **Explicit** | Specific file/line, clear command | Execute directly |
| **Exploratory** | "How does X work?", "Find Y" | Fire `@explore` (1-3 agents) + tools in parallel |
| **Open-ended** | "Improve", "Refactor", "Add feature" | Assess codebase first, then plan |
| **External** | Library questions, "how does [package] work?" | Delegate to `@librarian` |
| **Strategic** | Architecture decisions, 2+ failed attempts | Consult `@oracle` |
| **Ambiguous** | Unclear scope, multiple interpretations | Ask ONE clarifying question |

### Agent Delegation Triggers

| Pattern | Action |
|---------|--------|
| 2+ modules/directories involved | Fire `@explore` in background |
| External library/API mentioned | Fire `@librarian` in background |
| After completing significant implementation | Consult `@oracle` for review |
| After 2+ failed fix attempts | Consult `@oracle` for debugging strategy |
| "Where is X?" questions | Use `@explore` for fast search |

## Skills

Skills live in `skill/<name>/` with this structure:
```
skill/<name>/
├── SKILL.md          # Instructions and documentation
├── scripts/          # Executable scripts
├── references/       # Reference documentation
└── tests/            # Test files
```

### crawl4ai Skill

| Script                  | Purpose                      |
| ----------------------- | ---------------------------- |
| `basic_crawler.py`      | Single URL crawling          |
| `site_crawler.py`       | Multi-page site crawling     |
| `batch_crawler.py`      | Batch URL processing         |
| `extraction_pipeline.py`| Structured data extraction   |

Run with: `uvx --from crawl4ai python scripts/<script>.py`

## Gotchas

- Commands use YAML frontmatter — `---` delimiters required
- Model IDs must match provider format exactly (e.g., `amazon-bedrock/anthropic.claude-opus-4-20250514-v1:0`)
- Skills loaded via the `skill` tool — agents need `skill: allow` in permission
- `node_modules/` is gitignored — run `bun install` after clone
- **Markdown agent permissions**: Only simple `allow`/`ask`/`deny` values work for `bash` permissions in markdown agents. Granular patterns (e.g., `bash: { "mkdir *": allow }`) only work in JSON config, not YAML frontmatter.
- **Bash pattern bug** ([#6676](https://github.com/anomalyco/opencode/issues/6676)): Flags like `-p` are stripped during permission matching, so `mkdir -p foo` matches `mkdir`, not `mkdir -p *`

## Permissions (v1.1.1+)

As of v1.1.1, `tools` is **deprecated** and merged into `permission`. The `permission` field now controls both:
1. **Tool availability** - `"deny"` disables the tool entirely
2. **Approval requirements** - `"allow"` auto-approves, `"ask"` prompts user

### Permissionable Tools

Only these tools can be configured via `permission`:
- `edit` - File editing operations
- `bash` - Shell commands (supports granular patterns)
- `skill` - Loading agent skills
- `webfetch` - Fetching web pages
- `doom_loop` - Repeated identical tool calls
- `external_directory` - Access outside working directory

### Non-Permissionable Tools

These are **enabled by default** and can only be disabled via `tools: false`:
- `read`, `glob`, `grep`, `list` - Read-only tools (no approval needed)
- `write`, `patch` - Use `tools: false` to disable
- `todowrite`, `todoread`, `task` - Use `tools: false` to disable

### Bash Permission Pattern Matching

**Critical: Last matching rule wins.** When multiple patterns match a command, the rule defined **last** in the config takes precedence.

```jsonc
// WRONG - "*" at end overrides everything
"bash": {
  "git status*": "allow",
  "git commit*": "ask",
  "*": "ask"              // This matches last, so git status still asks!
}

// CORRECT - "*" first, specific rules override it
"bash": {
  "*": "ask",             // Default (matched first)
  "git status*": "allow", // Overrides default (matched last)
  "git commit*": "ask"
}
```

**Pattern syntax:**
- `*` matches zero or more characters
- `?` matches exactly one character
- All other characters match literally

### Agent Configuration Pattern (v1.1.1+)

```jsonc
"agent": {
  "my-agent": {
    "description": "...",
    "mode": "subagent",
    "prompt": "{file:./agent/my-agent.md}",
    // Disable non-permissionable tools you don't want
    "tools": {
      "write": false,
      "task": false
    },
    // Control permissionable tools via permission
    "permission": {
      "bash": {
        "*": "deny",              // Default FIRST (last matching wins)
        "git status": "allow",    // Specific rules override default
        "git diff *": "allow"
      },
      "edit": "deny",         // deny = edit tool disabled entirely
      "skill": "allow",       // allow = enabled, no approval needed
      "webfetch": "ask"       // ask = enabled, prompts for approval
    }
  }
}
```

### Permission Values

| Value | Effect |
|-------|--------|
| `"allow"` | Tool enabled, auto-approved (no prompt) |
| `"ask"` | Tool enabled, prompts user for approval |
| `"deny"` | Tool disabled entirely |
