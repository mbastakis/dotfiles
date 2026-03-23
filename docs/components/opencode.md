# OpenCode Configuration

Config model, agent definitions, custom commands, skills, and permission system.

**Source:** `private_dot_config/opencode/` -> `~/.config/opencode/`

**Isolated OMO Profile:** `private_dot_config/opencode-omo/` -> `~/.config/opencode-omo/`

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
    manager.md
    web-researcher.md
  command/                # Custom slash commands (markdown)
    commit.md
    crawl.md
    learn.md
    create_plan.md
    research_codebase.md
  skills/                 # Bundled skills shipped in source
    crawl4ai/
    linear-create/
    linear-list/
    linear-projects/
    linear-update/
    linear-workflow/
  plugins/                # Empty in source; runtime plugin install location

~/.config/opencode-omo/
  opencode.jsonc          # Minimal isolated config root for OMO
  oh-my-opencode.json     # OMO agent/category model profile
  tui.json                # TUI theme for the isolated profile
  .gitignore              # Ignores local package/plugin artifacts
  README.md               # Profile-local notes
```

_Reference: `private_dot_config/opencode/README.md:5`, `private_dot_config/opencode-omo/README.md:1`_

## Profiles

- `oc` uses the exported default profile rooted at `~/.config/opencode/`. `private_dot_config/zsh/exports.zsh:25`, `private_dot_config/zsh/aliases.zsh:59`
- `omo` overrides `OPENCODE_CONFIG` and `OPENCODE_CONFIG_DIR` for that invocation, so OpenCode reads from `~/.config/opencode-omo/` instead of the primary profile. `private_dot_config/zsh/aliases.zsh:60`
- The OMO profile enables `oh-my-opencode@latest` in its isolated `opencode.jsonc` and keeps the plugin's generated model profile in `oh-my-opencode.json`. `private_dot_config/opencode-omo/opencode.jsonc:1`, `private_dot_config/opencode-omo/oh-my-opencode.json:1`
- The checked-in OMO profile now pins explicit models per agent/category based on the published OMO model guidance, using locally available OpenAI, Google, OpenCode Zen, and Minimax/Kimi-backed model IDs rather than the installer's all-`gpt-5-nano` fallback. `private_dot_config/opencode-omo/oh-my-opencode.json:1`, `private_dot_config/opencode-omo/README.md:28`

## Config Model

The main config (`opencode.jsonc`) defines:

| Section | Purpose |
|---|---|
| `model` | Primary model (`openai/gpt-5.4`) |
| `theme` | `catppuccin` |
| `plugin` | Community plugins loaded from npm (for example `opencode-notifier`) |
| `permission` | Granular bash command permission rules |

Agent definitions live in `agent/*.md` as self-contained markdown files with YAML frontmatter (Pattern B). No agent blocks in `opencode.jsonc`.

_Reference: `private_dot_config/opencode/opencode.jsonc:1`_

## Linear CLI Setup

Linear operations are handled via `linear-cli` bash commands:

```bash
linear-cli i list --mine --output json --compact
```

Authentication is provided via `LINEAR_API_KEY` in `private_dot_config/zsh/local.zsh.tmpl`, and the manager agent is constrained to `linear-cli*` shell commands only.

_Reference: `private_dot_config/opencode/agent/manager.md`_

## Permission System

Bash command permissions use a **last matching rule wins** pattern:

| Pattern | Permission | Rationale |
|---|---|---|
| `*` | `ask` | Default: prompt for unknown commands |
| Read-only tools (grep, cat, ls, git status, etc.) | `allow` | Safe information gathering |
| Dangerous commands (sudo, rm -rf /, chown) | `deny` | Prevent destructive operations |
| Git write operations (commit, push, merge, rebase) | `ask` | Require confirmation |

**Tool types:**
- **Permissionable:** edit, bash, skill, webfetch, doom_loop, external_directory
- **Non-permissionable** (always allowed): read, glob, grep, write, patch

_Reference: `private_dot_config/opencode/README.md:69`_

## Agents

5 self-contained agents defined with YAML frontmatter (Pattern B — auto-discovered from `agent/`):

| Agent | Mode | Purpose | Key Constraints |
|---|---|---|---|
| `commit` | subagent | Git commit with pre-approved commands | Haiku model, minimal tools, git-only bash |
| `crawl` | subagent | Web crawling with crawl4ai | Haiku model, deny rm/curl/ssh/sudo |
| `librarian` | subagent | Research source code via `gh` CLI | Read-only, no file writes |
| `web-researcher` | subagent | Web research via DuckDuckGo/webfetch | Read-only, no file writes |
| `manager` | subagent | Linear project management | `linear-cli*` shell only, no web access |

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

### linear-* skills

Linear CLI helper skills for common PM operations:

- `linear-list` -- list/get issues and planning context
- `linear-create` -- create new issues with defaults and AC
- `linear-update` -- update status/labels/assignees/comments
- `linear-workflow` -- start/stop/close/assign flows
- `linear-projects` -- project and member operations

_Reference: `private_dot_config/opencode/skill/linear-list/SKILL.md`_

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
