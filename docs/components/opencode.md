# OpenCode Configuration

Config model, agent definitions, custom commands, skills, and permission system.

**Source:** `private_dot_config/opencode/` -> `~/.config/opencode/`

## Directory Structure

```
~/.config/opencode/
  opencode.jsonc          # Main config (model, theme, permissions, agents)
  agent/                  # Custom agent definitions (markdown + YAML frontmatter)
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
  plans/                  # Plan output directory
  skill/                  # Bundled skills
    aws-login/            # AWS/kubectl environment and wrapper guidance
    crawl4ai/             # Web crawling skill (SKILL.md + scripts/ + references/)
  workflows/              # Manager agent workflows
    manager/
      classification.md
      analysis/workflow.md
      architecture/workflow.md
      bug-fix/workflow.md
      epic/workflow.md
      implementation/workflow.md
      quick-task/workflow.md
      research/workflow.md
```

_Reference: `private_dot_config/opencode/README.md:5`_

## Config Model

The main config (`opencode.jsonc`) defines:

| Section | Purpose |
|---|---|
| `model` | Primary model (`claude-opus-4-5` via Amazon Bedrock) |
| `theme` | `catppuccin` |
| `permission` | Granular bash command permission rules |
| `agent` | 5 custom agent definitions |

_Reference: `private_dot_config/opencode/opencode.jsonc:1`_

## Linear CLI Setup

Linear operations are handled via `linear-cli` bash commands:

```bash
linear-cli i list --mine --output json --compact
```

Authentication is provided via `LINEAR_API_KEY` in `dot_zsh/local.zsh.tmpl`, and the manager agent is constrained to `linear-cli*` shell commands only.

_Reference: `private_dot_config/opencode/opencode.jsonc:269`_

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

_Reference: `private_dot_config/opencode/README.md:23`_

## Agents

5 custom agents defined with markdown files and YAML frontmatter:

| Agent | Mode | Purpose | Key Constraints |
|---|---|---|---|
| `librarian` | -- | Research source code via `gh` CLI | Read-only, no file writes |
| `commit` | -- | Git commit with pre-approved commands | Minimal tools |
| `crawl` | -- | Web crawling with crawl4ai | Deny rm/curl/ssh/sudo |
| `web-researcher` | -- | Web research via DuckDuckGo/webfetch | Read-only |
| `manager` | `all` (tab-switchable) | Linear project management | Read-only files, `linear-cli*` shell only |

The manager agent uses BMAD-style workflows with classification triggers (`[RW]` for research, `[CE]` for epic creation, etc.) and is the designated handler for all Linear operations.

_Reference: `private_dot_config/opencode/AGENTS.md:45`_

## Custom Commands

| Command | File | Purpose |
|---|---|---|
| `/commit` | `command/commit.md` | Guided git commit |
| `/crawl` | `command/crawl.md` | Crawl a URL with crawl4ai |
| `/learn` | `command/learn.md` | Learn from documentation |
| `/create_plan` | `command/create_plan.md` | Create an implementation plan |
| `/research_codebase` | `command/research_codebase.md` | Research the current codebase |

_Reference: `private_dot_config/opencode/README.md:15`_

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

## Manager Workflows

The manager agent has structured workflows for different task types:

| Workflow | Trigger | Purpose |
|---|---|---|
| `classification.md` | Automatic | Classify incoming requests |
| `research/workflow.md` | `[RW]` | Research and analysis |
| `epic/workflow.md` | `[CE]` | Create epics with stories |
| `implementation/workflow.md` | `[CI]` | Implementation planning |
| `quick-task/workflow.md` | `[QT]` | Fast issue creation |
| `bug-fix/workflow.md` | `[BF]` | Bug investigation and fix |
| `analysis/workflow.md` | `[AN]` | Deep analysis |
| `architecture/workflow.md` | `[AR]` | Architecture decisions |

_Reference: `private_dot_config/opencode/workflows/manager/`_

## Gotchas

- Agent markdown files use YAML frontmatter delimiters (`---`); syntax must be exact.
- Model IDs must match the provider's exact format (e.g., `amazon-bedrock/anthropic.claude-opus-4-5-...`).
- Markdown agents only support simple `allow`/`ask`/`deny` permissions, not granular bash patterns.
- `package.json` and `bun.lock` under `.config/opencode/` are repo-ignored artifacts and should stay in `.chezmoiignore`.

_Reference: `private_dot_config/opencode/README.md:40`_

## References

- Main config: `private_dot_config/opencode/opencode.jsonc:1`
- README: `private_dot_config/opencode/README.md:1`
- AGENTS: `private_dot_config/opencode/AGENTS.md:1`
- Manager workflows: `private_dot_config/opencode/workflows/manager/`
