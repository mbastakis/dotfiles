# OpenCode Configuration

Custom commands, agents, and skills for OpenCode AI assistant.

## Structure

| Path               | Purpose                                  |
| ------------------ | ---------------------------------------- |
| `opencode.jsonc`   | Main config (provider, global permissions) |
| `command/*.md`     | Custom slash commands                    |
| `agent/*.md`       | Self-contained agents (YAML frontmatter) |
| `skill/*/SKILL.md` | Skills with scripts and references       |

## Commands

| Command       | Purpose              |
| ------------- | -------------------- |
| `opencode`    | Start OpenCode       |
| `oc`          | Alias for opencode   |
| `bun install` | Install dependencies |

## Custom Commands

Create `command/<name>.md` with YAML frontmatter:

```markdown
---
description: Brief description shown in command list
agent: optional-agent-routing
subtask: true
---

# Command Title

Instructions for the command in markdown...
```

**Current commands**:

- `commit.md` — Guided git commit (routes to `@commit`, subtask)
- `crawl.md` — Crawl a URL with crawl4ai (routes to `@crawl`, subtask)
- `research_codebase.md` — Document codebase through parallel research (subtask)
- `create_plan.md` — Create detailed implementation plans
- `learn.md` — Learn from documentation

## Custom Agents (Pattern B — Self-Contained .md)

Each agent is a single `.md` file with YAML frontmatter containing all config (description, mode, model, temperature, tools, permissions) plus the prompt body:

```markdown
---
description: Brief description of what the agent does
mode: subagent
model: provider/model-id
temperature: 0.5
tools:
  write: false
  patch: false
permission:
  bash:
    "*": deny
    "git*": allow
  edit: deny
  skill: allow
  webfetch: allow
  external_directory: allow
---

You are an agent that does X.

## Methodology
...

## Output Format
...

## Guardrails
...
```

No agent blocks needed in `opencode.jsonc` — agents are auto-discovered from the `agent/` directory.

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

### Permission Values

| Value     | Effect                                  |
| --------- | --------------------------------------- |
| `"allow"` | Tool enabled, auto-approved (no prompt) |
| `"ask"`   | Tool enabled, prompts user for approval |
| `"deny"`  | Tool disabled entirely                  |

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

| Script                   | Purpose                    |
| ------------------------ | -------------------------- |
| `basic_crawler.py`       | Single URL crawling        |
| `site_crawler.py`        | Multi-page site crawling   |
| `batch_crawler.py`       | Batch URL processing       |
| `extraction_pipeline.py` | Structured data extraction |

## Gotchas

- Commands use YAML frontmatter — `---` delimiters required
- Model IDs must match provider format exactly (e.g., `amazon-bedrock/anthropic.claude-opus-4-20250514-v1:0`)
- Skills loaded via the `skill` tool — agents need `skill: allow` in permission
- `node_modules/` is gitignored — run `bun install` after clone
- **Bash pattern bug** ([#6676](https://github.com/anomalyco/opencode/issues/6676)): Flags like `-p` are stripped during permission matching, so `mkdir -p foo` matches `mkdir`, not `mkdir -p *`
