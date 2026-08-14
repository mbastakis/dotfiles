# OpenCode Configuration

Custom commands, agents, and skills for OpenCode AI assistant.

## Structure

| Path               | Purpose                                  |
| ------------------ | ---------------------------------------- |
| `opencode.jsonc`   | Main config (provider, global permissions) |
| `command/*.md`     | Custom slash commands                    |
| `agent/*.md`       | Self-contained agents (YAML frontmatter) |
| `skills/*/SKILL.md` | OpenCode-only skills with scripts and references |
| `plugins/*.js`     | Local OpenCode plugins loaded by `opencode.jsonc` |
| `~/.agents/skills/*/SKILL.md` | Shared harness-agnostic skills managed from `private_dot_agents/skills/` |

## Commands

| Command       | Purpose              |
| ------------- | -------------------- |
| `opencode`    | Start OpenCode       |
| `oc`          | Alias for opencode   |
| `bun install` | Install dependencies |

## Providers

WCS routes all configured GPT and lightweight model requests through the private WhoCaresSoftware gateway at `https://ai.whocaressoftware.com/v1`. Direct OpenAI OAuth and API-key providers are not configured or enabled. Direct OpenCode Zen (`opencode`) remains allowlisted for explicit free-model selection. The live WCS gateway currently exposes the short aliases `gpt`, `deepseek`, `glm`, `kimi`, `qwen`, and `minimax`.

| Model ID | Purpose | Variants |
| -------- | ------- | -------- |
| `opencode/*` | Selected free OpenCode Zen models via `https://opencode.ai/zen/v1` | Per-model Models.dev metadata |
| `wcs/gpt` | Default GPT-5.6 Sol through WCS ChatGPT OAuth | `none`, `low`, `medium`, `high`, `xhigh`, `max` reasoning effort |
| `wcs/deepseek` | DeepSeek V4 Pro through WCS OpenCode Go | `high`, `max` reasoning effort |
| `wcs/glm` | GLM-5.2 through WCS OpenCode Go | `high`, `max` reasoning effort |
| `wcs/kimi` | Kimi K2.7 Code through WCS OpenCode Go | none; Models.dev lists no reasoning options |
| `wcs/qwen` | Qwen3.7 Max through WCS OpenCode Go | `off`, `on`, `max` thinking; max budget `262144` |
| `wcs/minimax` | MiniMax-M3 through WCS OpenCode Go | `off`, `on` thinking |

Selected direct OpenCode Zen free models: `opencode/big-pickle`, `opencode/deepseek-v4-flash-free`, `opencode/glm-5-free`, `opencode/grok-code`, `opencode/hy3-preview-free`, `opencode/kimi-k2.5-free`, `opencode/ling-2.6-flash-free`, `opencode/mimo-v2.5-free`, `opencode/minimax-m3-free`, `opencode/nemotron-3-ultra-free`, `opencode/north-mini-code-free`, `opencode/qwen3.6-plus-free`, `opencode/ring-2.6-1t-free`, and `opencode/trinity-large-preview-free`.

Commented-out WCS aliases: `deepseek-v4-flash`, `deepseek-v4-pro`, `glm-5.2`, `kimi-k2.7-code`, `qwen3.6-plus`, and `minimax-m3`. They need matching LiteLLM `model_name` routes on the WCS VM before they can be enabled in the client config.

The `-fast` suffix is an actual OAuth-provider model variant. It is used where lower latency matters more than maximum reasoning depth.

Shell aliases:

```bash
oc-sub   # shared configured default
oc-oauth # shared configured default
```

`enabled_providers` is set to `["opencode", "selfhosted", "wcs"]`.

The `selfhosted` provider reaches the V100 model server directly at
`192.168.179.112:8080` through the `Hendriks Machine dgx1` WireGuard tunnel.
It exposes `selfhosted/qwen3-coder-next`, `selfhosted/glm-4.7-flash`, and
`selfhosted/minimax-m2.7`; only the model currently selected on the server is
available at a time. The API key
comes from `SELFHOSTED_LLM_API_KEY`, rendered into `~/.config/zsh/local.zsh` so
the launchd-managed OpenCode server receives it as well as interactive shells.

Qwen3 Coder Next is officially non-thinking. GLM 4.7 Flash exposes `off`,
`thinking-8k`, `thinking`, and `preserved` variants. Models.dev documents a
native thinking toggle; `thinking-8k` is an explicit llama.cpp token cap rather
than a model-native effort level, while `preserved` retains prior reasoning for
multi-turn agent work. MiniMax M2.7 is the strongest local coding-agent model;
it runs at 32K context and retains interleaved reasoning for tool-driven turns.

## Plugins

- `plugins/tmux-session-state.js` records OpenCode session lifecycle events into `~/.local/state/opencode/tmux-session-state/`. The TUI plugin publishes its current session by client PID and, when applicable, tmux pane. The picker prunes dead clients and pane mappings that no longer own their TTY. `~/bin/opencode-session-picker` exposes attached panes plus live non-tmux TUI sessions to the collapsible sidebar. Each session uses a two-line Nerd Font status, summary, and model block; selecting an attached row focuses its pane, while an unopened row creates a window in the matching tmux session. Questions and permission requests from subagents mark their top-level session as blocked so the visible sidebar row requests attention.
- `plugins/clickable-notifier.js` sends sound/desktop alerts for primary-session events and promotes subagent questions and permission requests to their top-level session. Each alert names the state, project, OpenCode task title, and exact tmux target. Questions show the question, permission alerts show the requested patterns, errors show the failure message, and completions include a shortened version of the latest assistant response. On macOS it uses `terminal-notifier` so clicking an alert runs `~/bin/opencode-focus-session`, activates Ghostty, and selects the recorded tmux pane. On the remote host it publishes the same structured content through the local PWA Web Push companion with a direct session route. Built-in TUI attention is disabled in `tui.json` so it does not emit separate `subagent_done` sounds.
- `plugins/descendant-skills.js` exposes descendant `.opencode/{skill,skills}` and `.agents/{skill,skills}` roots through the opened project's native `.opencode/skills/.descendant-skills/` tree and also adds them to its configured skill paths. The native projection works around OpenCode 1.18.15's plugin/skill initialization race without making the skills global. It scans only below the project root, stays on the same filesystem, does not follow directory symlinks, and prunes version-control, dependency, cache, and build trees. The plugin owns only symlinks inside `.descendant-skills`; other entries are left untouched. New descendant skills become visible after the project instance is reopened; OpenCode retains its native duplicate-name handling.

Restart OpenCode after changing plugin files or the `plugin` array; running panes keep the config loaded at process start.

The designated host exposes `opencode-serverctl` for managing the shared backend, PWA push, and oauth2-proxy LaunchAgents:

```bash
opencode-serverctl status          # all services and HTTP health
opencode-serverctl restart server  # backend only
opencode-serverctl restart pwa     # PWA push only
opencode-serverctl disable         # persistently disable both services
opencode-serverctl enable          # enable, start, and health-check both
opencode-serverctl logs proxy      # follow proxy stdout and stderr
```

`start` and `stop` only change the current launchd login session. `enable` and `disable` also update launchd's persistent disabled state. Commands default to `all`; use `server`, `pwa`, or `proxy` to target one component.

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
- `research_codebase.md` — Document codebase through parallel `@explore` research
- `create_plan.md` — Create detailed implementation plans (`@plan`, active/default model)
- `learn.md` — Extract non-obvious learnings into AGENTS.md files (inherits the active model and variant)
- `session_analysis.md` — Export and analyze a previous OpenCode session (`@general`, subtask)

## Custom Agents (Pattern B — Self-Contained .md)

Each agent is a single `.md` file with YAML frontmatter containing its config (description, mode, optional model, temperature, tools, permissions) plus the prompt body:

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

The title agent is pinned in `opencode.jsonc`; all other agents inherit the active model and variant.

| Agent | Model Selection | Purpose |
| ----- | --------------- | ------- |
| `build` | Active/session model, then global default | Primary implementation agent |
| `plan` | Active/session model, then global default | Planning and no-edit reasoning |
| `general` | Inherits parent model and variant | Broad subagent work |
| `explore` | `wcs/gpt-5.5` (`none`) | Fast repo exploration without reasoning overhead |
| `title` | `opencode/big-pickle` | Session titles using the free OpenCode Zen model |
| `summary` | No LLM call in OpenCode 1.17.19 | Snapshot and file-diff metadata |
| `compaction` | Inherits triggering model and variant | Conversation compaction |

Custom agents inherit the parent model and variant:

| Agent | Model Selection | Purpose |
| ----- | --------------- | ------- |
| `commit` | Inherits parent model and variant | Git commit planning and execution |
| `crawl` | Inherits parent model and variant | crawl4ai execution |
| `librarian` | Inherits parent model and variant | External source/GitHub forensics with permalinks |
| `web-researcher` | Inherits parent model and variant | Web documentation and synthesis |

OpenCode removed its experimental Scout agent before 1.17.19. Use `explore` for local codebase reconnaissance, `librarian` for upstream implementation forensics, and `web-researcher` for documentation and comparisons.

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

OpenCode scans both OpenCode-specific skills in `~/.config/opencode/skills/` and shared Agent Skills in `~/.agents/skills/`. Shared skills are managed from `private_dot_agents/skills/` so Pi can load the same skill definitions.

OpenCode-only skills live in `skills/<name>/` with this structure:

```
skills/<name>/
├── SKILL.md          # Instructions and documentation
├── scripts/          # Executable scripts
├── references/       # Reference documentation
└── tests/            # Test files
```

### Shared Skills

- `grill-with-docs` lives in `~/.agents/skills/grill-with-docs/` and is intentionally harness-agnostic.
- `writing-great-skills` lives in `~/.agents/skills/writing-great-skills/` and documents skill-writing vocabulary and structure.
- `teach` lives in `~/.agents/skills/teach/` and supports stateful teaching workspaces with mission-grounded lessons, resources, glossaries, and learning records.

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
