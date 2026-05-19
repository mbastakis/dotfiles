# OpenCode Configuration

Config model, agent definitions, custom commands, skills, and permission system.

**Source:** `private_dot_config/opencode/` -> `~/.config/opencode/`

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
  skills/                 # Bundled skills shipped in source
    crawl4ai/
    skill-creator/
  plugins/                # Empty in source; runtime plugin install location
```

_Reference: `private_dot_config/opencode/README.md:5`_

## Profiles

- `oc` uses the exported default profile rooted at `~/.config/opencode/`. `private_dot_config/zsh/exports.zsh:25`, `private_dot_config/zsh/aliases.zsh:59`

## Config Model

The main config (`opencode.jsonc`) defines:

| Section | Purpose |
|---|---|
| `model` | Primary model (`openai/gpt-5.5`, subscription-backed by default) |
| `provider.openai-api` | OpenAI API-key aliases (`openai-api/gpt-5.4`, `openai-api/gpt-5.5`) using `OPENAI_API_KEY` |
| `theme` | `catppuccin` |
| `mcp` | Remote MCP servers, disabled by default unless explicitly enabled |
| `plugin` | Community plugins loaded from npm (for example `opencode-notifier`) |
| `permission` | Granular bash command permission rules |

Agent definitions live in `agent/*.md` as self-contained markdown files with YAML frontmatter (Pattern B). No agent blocks in `opencode.jsonc`.

_Reference: `private_dot_config/opencode/opencode.jsonc:1`_

## OpenAI Auth Selection

OpenAI subscription and API-key usage are split across two provider IDs:

| Model ID | Auth Source | Use Case |
|---|---|---|
| `openai/gpt-5.5` | Built-in OpenAI auth via `opencode auth login -p openai` | ChatGPT Plus/Pro subscription |
| `openai-api/gpt-5.4` | `OPENAI_API_KEY` or stored `openai-api` key | OpenAI API billing |
| `openai-api/gpt-5.5` | `OPENAI_API_KEY` or stored `openai-api` key | OpenAI API billing |

Switch per run with `opencode -m openai/gpt-5.5`, `opencode -m openai-api/gpt-5.4`, or `opencode -m openai-api/gpt-5.5`. Shell aliases make the split explicit: `oc-sub` launches subscription-backed `openai/gpt-5.5`, and `oc-api` launches API-key-backed `openai-api/gpt-5.5`. In the TUI, use `/models` and choose either OpenAI or OpenAI API EU.

The `openai-api` aliases are hand-curated. `openai-api/gpt-5.5` includes explicit USD-per-1M-token pricing so `opencode stats` can show spend; custom aliases do not inherit pricing metadata from the built-in OpenAI provider.

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

4 self-contained agents defined with YAML frontmatter (Pattern B — auto-discovered from `agent/`):

| Agent | Mode | Purpose | Key Constraints |
|---|---|---|---|
| `commit` | subagent | Git commit with pre-approved commands | Haiku model, minimal tools, git-only bash |
| `crawl` | subagent | Web crawling with crawl4ai | Haiku model, deny rm/curl/ssh/sudo |
| `librarian` | subagent | Research source code via `gh` CLI | Read-only, no file writes |
| `web-researcher` | subagent | Web research via DuckDuckGo/webfetch | Read-only, no file writes |

Each agent file contains its own description, mode, model, temperature, tools, and permissions in YAML frontmatter, plus the prompt body below.

_Reference: `private_dot_config/opencode/AGENTS.md:1`_

## Custom Commands

| Command | File | Purpose |
|---|---|---|
| `/commit` | `command/commit.md` | Guided git commit (subtask, routes to `@commit`) |
| `/crawl` | `command/crawl.md` | Crawl a URL with crawl4ai (subtask, routes to `@crawl`) |
| `/learn` | `command/learn.md` | Learn from documentation |
| `/create_plan` | `command/create_plan.md` | Create an implementation plan |
| `/research_codebase` | `command/research_codebase.md` | Research the current codebase (subtask) |

_Reference: `private_dot_config/opencode/README.md:24`_

## Skills

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
