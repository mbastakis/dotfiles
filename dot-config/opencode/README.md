# OpenCode Configuration

Custom commands, agents, and skills for OpenCode AI assistant.

## Structure

| Path               | Purpose                                  |
| ------------------ | ---------------------------------------- |
| `opencode.jsonc`   | Main config (provider, MCP, permissions) |
| `command/*.md`     | Custom slash commands                    |
| `agent/*.md`       | Custom subagents                         |
| `workflows/`       | BMAD-style workflow definitions          |
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
- **Markdown agent permissions**: Only simple `allow`/`ask`/`deny` values work for `bash` permissions in markdown agents. Granular patterns (e.g., `bash: { "mkdir *": allow }`) only work in JSON config, not YAML frontmatter.
- **Bash pattern bug** ([#6676](https://github.com/anomalyco/opencode/issues/6676)): Flags like `-p` are stripped during permission matching, so `mkdir -p foo` matches `mkdir`, not `mkdir -p *`
