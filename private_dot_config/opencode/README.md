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

## OpenAI Auth

Only the built-in OpenAI provider is enabled, so all configured models use OAuth subscription auth from `opencode auth login -p openai`.

| Model ID | Purpose |
| -------- | ------- |
| `openai/gpt-5.5` | Default high-quality fallback, planning, broad research |
| `openai/gpt-5.3-codex` | Coding, source research, repo scouting |
| `openai/gpt-5.4-mini-fast` | Fast bounded tasks, exploration, titles, small model fallback |
| `openai/gpt-5.4` | Conversation compaction |

The `-fast` suffix is an actual OAuth-provider model variant. It is used where lower latency matters more than maximum reasoning depth.

Shell aliases:

```bash
oc-sub   # subscription: openai/gpt-5.5
oc-oauth # subscription: openai/gpt-5.5
```

Auth setup:

```bash
opencode auth login -p openai
# choose ChatGPT Plus/Pro for subscription auth
```

`enabled_providers` is set to `["openai"]`; API-key providers are intentionally unavailable unless that allowlist is changed.

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
- `research_codebase.md` — Document codebase through parallel research (`openai/gpt-5.3-codex`)
- `create_plan.md` — Create detailed implementation plans (`@plan`, `openai/gpt-5.5`)
- `learn.md` — Extract non-obvious learnings into AGENTS.md files (`openai/gpt-5.4-mini-fast`)

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

Custom agent blocks are not needed in `opencode.jsonc` because agents are auto-discovered from the `agent/` directory.

Built-in agents are configured in `opencode.jsonc`:

| Agent | Model | Purpose |
| ----- | ----- | ------- |
| `build` | `openai/gpt-5.3-codex` | Code implementation |
| `plan` | `openai/gpt-5.5` | Planning and no-edit reasoning |
| `general` | `openai/gpt-5.5` | Broad subagent work |
| `explore` | `openai/gpt-5.4-mini-fast` | Fast repo exploration |
| `scout` | `openai/gpt-5.3-codex` | Manual broad reference/repo scouting |
| `title` | `openai/gpt-5.4-mini-fast` | Session titles |
| `summary` | `openai/gpt-5.4-mini-fast` | Lightweight summaries |
| `compaction` | `openai/gpt-5.4` | Conversation compaction |

Custom agents set their model in frontmatter:

| Agent | Model | Purpose |
| ----- | ----- | ------- |
| `commit` | `openai/gpt-5.4-mini-fast` | Git commit planning and execution |
| `crawl` | `openai/gpt-5.4-mini-fast` | crawl4ai execution |
| `librarian` | `openai/gpt-5.3-codex` | External source/GitHub forensics with permalinks |
| `web-researcher` | `openai/gpt-5.5` | Web documentation and synthesis |

Role split: `@scout` is user-invoked for broad reconnaissance, while `librarian` is for source-backed implementation and change-history answers.

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

The global `opencode.jsonc` policy is intentionally permissive: `edit` and `external_directory` are allowed, and bash defaults to `"*": "allow"`. Only specific risky commands are changed back to `"ask"`, including destructive filesystem commands, git remote/history changes, mutating `kubectl`/`helm` commands, and risky `terraform`/`tofu` commands.

Because OpenCode may normalize command flags before bash permission matching, broad patterns like `"rm*"`, `"chmod*"`, and `"chown*"` are used to ensure recursive forms such as `rm -rf` still prompt. For CLI tools that support flags before the subcommand, both forms are listed, for example `"kubectl apply*"` and `"kubectl * apply*"`.

```jsonc
// WRONG - "*" at end overrides everything
"bash": {
  "git push*": "ask",
  "kubectl apply*": "ask",
  "*": "allow"            // This matches last, so nothing asks!
}

// CORRECT - "*" first, specific rules override it
"bash": {
  "*": "allow",           // Default (matched first)
  "git push*": "ask",
  "kubectl apply*": "ask"
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
