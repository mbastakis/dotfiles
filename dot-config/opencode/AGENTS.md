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
- `web-researcher.md` — Search the web and synthesize findings
- `web-crawler.md` — Crawl websites and persist to ai-docs (configured in opencode.jsonc)

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
        "git status": "allow",
        "git diff *": "allow",
        "*": "deny"           // deny = tool disabled for this pattern
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
