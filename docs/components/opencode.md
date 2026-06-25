# OpenCode Configuration

Config model, agent definitions, custom commands, skills, and permission system.

**Source:** `private_dot_config/opencode/` -> `~/.config/opencode/`

Shared harness-agnostic skills are managed separately from `private_dot_agents/skills/` -> `~/.agents/skills/`. OpenCode auto-loads that external skill location alongside `~/.config/opencode/skills/`.

## Directory Structure

```
~/.config/opencode/
  opencode.jsonc          # Main config (model, global permissions)
  opencode-notifier.json  # Notification plugin settings
  tui.json                # TUI theme
  AGENTS.md               # Delegation guidance
  agent/                  # Self-contained agents (YAML frontmatter + prompt)
    commit.md
    crawl.md
    librarian.md
    web-researcher.md
  command/                # Custom slash commands (markdown)
    commit.md
    crawl.md
    learn.md
    create_plan.md
    research_codebase.md
    session_analysis.md
  skills/                 # OpenCode-only bundled skills shipped in source
    crawl4ai/
    skill-creator/
  plugins/                # Empty in source; runtime plugin install location
```

_Reference: `private_dot_config/opencode/README.md:5`_

## Profiles

- `oc` uses the exported default profile rooted at `~/.config/opencode/`. `oc-sub` and `oc-oauth` explicitly select `openai/gpt-5.5`. `private_dot_config/zsh/exports.zsh:25`, `private_dot_config/zsh/aliases.zsh:59`

## Config Model

The main config (`opencode.jsonc`) defines:

| Section | Purpose |
|---|---|
| `model` | Primary model (`openai/gpt-5.5`, subscription-backed by default) |
| `small_model` | Lightweight fallback model (`openai/gpt-5.4-mini-fast`) |
| `enabled_providers` | Restricts available providers to OAuth-backed `openai` |
| `provider.openai` | OpenAI OAuth provider options, including EU base URL |
| `agent` | Explicit built-in agent model overrides |
| `mcp` | Remote MCP servers, disabled by default unless explicitly enabled |
| `plugin` | Community plugins loaded from npm (for example `opencode-notifier`) |
| `permission` | Granular bash command permission rules |

Custom agent definitions live in `agent/*.md` as self-contained markdown files with YAML frontmatter (Pattern B). Built-in agent model overrides live in `opencode.jsonc`.

_Reference: `private_dot_config/opencode/opencode.jsonc:1`_

## OpenAI Auth

Only the built-in OpenAI provider is enabled, so configured models use OAuth subscription auth from `opencode auth login -p openai`.

| Model ID | Use Case |
|---|---|
| `openai/gpt-5.5` | Default high-quality fallback, planning, broad research |
| `openai/gpt-5.4-mini-fast` | Fast bounded tasks, exploration, titles, small model fallback |
| `openai/gpt-5.4` | Source research, repo scouting, conversation compaction |

The `-fast` suffix is an actual OAuth-provider model variant. It is used where lower latency matters more than maximum reasoning depth. `enabled_providers` is set to `["openai"]`; API-key providers are intentionally unavailable unless that allowlist is changed. Shell aliases `oc-sub` and `oc-oauth` both launch subscription-backed `openai/gpt-5.5`.

## MCP Servers

MCP servers are configured globally but left disabled by default so they do not add tools or authentication prompts unless explicitly enabled.

| Server | Type | Default | Purpose |
|---|---|---|---|
| `pocketsmith` | remote | disabled | PocketSmith MCP endpoint |
| `telecontext` | remote | disabled | Deutsche Telekom Telecontext MCP endpoint at `https://telecontext.trap.ng.telekom.net/mcp` |

Enable and authenticate MCP servers from OpenCode only when needed, for example with `/mcp` in the TUI or the relevant `opencode mcp` command.

## Permission System

Global permissions are default-allow for a freer primary agent:

| Pattern | Permission | Rationale |
|---|---|---|
| `edit` | `allow` | File edits do not prompt by default |
| `external_directory` | `allow` | Work outside the repo is allowed by default |
| Bash `*` | `allow` | Unknown commands run without approval |
| `rm*`, `rmdir*`, `chmod*`, `chown*`, `sudo`, `su` | `ask` | Prompt for destructive or privileged filesystem operations |
| `git push*`, `git reset*`, `git clean*`, `git rm*`, `git rebase*` | `ask` | Require confirmation for remote/history-destructive git operations |
| Mutating `kubectl`/`helm`, risky `terraform`/`tofu` commands | `ask` | Require confirmation for cluster and infrastructure changes |

Bash command permissions still use **last matching rule wins**, so broad `"*": "allow"` must stay before the specific `"ask"` patterns. Patterns include common flag-before-subcommand forms such as `kubectl * apply*` and `git * push*`. Specialized subagents can override the global policy with their own stricter permissions.

**Tool types:**
- **Permissionable:** edit, bash, skill, webfetch, doom_loop, external_directory
- **Non-permissionable** (always allowed): read, glob, grep, write, patch

_Reference: `private_dot_config/opencode/README.md:69`_

## Agents

4 self-contained custom agents are defined with YAML frontmatter (Pattern B — auto-discovered from `agent/`). Explicit built-in agent overrides live in `opencode.jsonc`.

| Agent | Mode | Purpose | Key Constraints |
|---|---|---|---|
| `commit` | subagent | Git commit with pre-approved commands | `openai/gpt-5.4-mini-fast`, minimal tools, git-only bash |
| `crawl` | subagent | Web crawling with crawl4ai | `openai/gpt-5.4-mini-fast`, deny rm/curl/ssh/sudo |
| `librarian` | subagent | External source/GitHub forensics with permalink evidence | `openai/gpt-5.4`, read-only, no file writes |
| `web-researcher` | subagent | Web research via DuckDuckGo/webfetch | `openai/gpt-5.5`, read-only, no file writes |

Role split: `@scout` is user-invoked for broad reconnaissance, while `librarian` is used for source-backed implementation and change-history analysis.

Each agent file contains its own description, mode, model, temperature, tools, and permissions in YAML frontmatter, plus the prompt body below.

Built-in model overrides. `build` uses the global default model.

| Agent | Model | Purpose |
|---|---|---|
| `plan` | `openai/gpt-5.5` | Planning and no-edit reasoning |
| `general` | `openai/gpt-5.5` | Broad subagent work |
| `explore` | `openai/gpt-5.4-mini-fast` | Fast repo exploration |
| `scout` | `openai/gpt-5.4` | Manual broad reference/repo scouting |
| `title` | `openai/gpt-5.4-mini-fast` | Session titles |
| `summary` | `openai/gpt-5.4-mini-fast` | Lightweight summaries |
| `compaction` | `openai/gpt-5.4` | Conversation compaction |

_Reference: `private_dot_config/opencode/AGENTS.md:1`_

## Custom Commands

| Command | File | Purpose |
|---|---|---|
| `/commit` | `command/commit.md` | Guided git commit (subtask, routes to `@commit`) |
| `/crawl` | `command/crawl.md` | Crawl a URL with crawl4ai (subtask, routes to `@crawl`) |
| `/learn` | `command/learn.md` | Extract AGENTS.md learnings with `openai/gpt-5.4-mini-fast` |
| `/create_plan` | `command/create_plan.md` | Create an implementation plan with `@plan` and `openai/gpt-5.5` |
| `/research_codebase` | `command/research_codebase.md` | Research the current codebase with `openai/gpt-5.4` |
| `/session_analysis` | `command/session_analysis.md` | Export and analyze a previous OpenCode session with `@scout` |

_Reference: `private_dot_config/opencode/README.md:24`_

## Skills

OpenCode discovers two managed skill classes:

| Class | Source | Target | Use |
|---|---|---|---|
| OpenCode-only | `private_dot_config/opencode/skills/` | `~/.config/opencode/skills/` | Skills that depend on OpenCode workflows or tooling |
| Shared Agent Skills | `private_dot_agents/skills/` | `~/.agents/skills/` | Harness-agnostic skills loaded by both OpenCode and Pi |

### grill-with-docs

Shared skill for stress-testing plans against a repository's domain language and documented decisions. It uses `CONTEXT.md` as a glossary and offers ADRs only for hard-to-reverse, surprising trade-offs.

_Reference: `private_dot_agents/skills/grill-with-docs/SKILL.md`_

### aws-login

Bundled skill for safe AWS and kubectl usage through the `aws-login` CLI wrapper:

- Defines required command pattern: `aws-login exec <env> -- <tool> <command>`
- Documents environment mapping for `playground`, `dev`, and `prod`
- Enforces a preflight protocol (context check, history check, context alignment)
- Includes examples for both `kubectl` and `aws` commands

_Reference: `private_dot_config/opencode/skill/aws-login/SKILL.md`_

### crawl4ai

Bundled skill for web crawling and data extraction:

- `SKILL.md` -- complete instructions and usage patterns
- `scripts/` -- Python crawling scripts (adaptive, basic, batch, extraction pipeline, site crawler)
- `references/` -- SDK reference documentation
- `tests/` -- Test suite for crawling functionality

Loaded by agents via `skill({ name: "crawl4ai" })`.

_Reference: `private_dot_config/opencode/skill/crawl4ai/SKILL.md`_

## Gotchas

- Agent markdown files use YAML frontmatter delimiters (`---`); syntax must be exact.
- Model IDs must match the provider's exact format (e.g., `amazon-bedrock/anthropic.claude-opus-4-5-...`).
- Granular bash patterns in YAML frontmatter work correctly (confirmed via OpenCode source).
- `package.json` and `bun.lock` under `.config/opencode/` are repo-ignored artifacts and should stay in `.chezmoiignore`.

_Reference: `private_dot_config/opencode/README.md:131`_

## References

- Main config: `private_dot_config/opencode/opencode.jsonc:1`
- README: `private_dot_config/opencode/README.md:1`
- AGENTS: `private_dot_config/opencode/AGENTS.md:1`
