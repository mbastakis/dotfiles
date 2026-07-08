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
  plugins/
    tmux-session-state.js # Local plugin that records tmux pane/session status
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
| `enabled_providers` | Restricts available providers to `openai`, `openai-api`, `opencode`, and `wcs` |
| `provider.openai` | OpenAI OAuth provider options, including EU base URL |
| `provider.openai-api` | OpenAI API-key provider options, including EU base URL |
| `provider.opencode` | Direct OpenCode Zen provider for selected free models, authenticated with `OPENCODE_API_KEY` |
| `provider.wcs` | WCS OpenAI-compatible provider, authenticated with `WCS_API_KEY` |
| `agent` | Small-job built-in agent model overrides |
| `mcp` | Remote MCP servers, disabled by default unless explicitly enabled |
| `plugin` | Community plugins loaded from npm (for example `opencode-notifier`) |
| `permission` | Granular bash command permission rules |

Custom agent definitions live in `agent/*.md` as self-contained markdown files with YAML frontmatter (Pattern B). Larger agents and commands omit `model` so they inherit the active/default model; only bounded small jobs pin a model.

The local `plugins/tmux-session-state.js` plugin listens to OpenCode session lifecycle events and writes per-session state under `~/.local/state/opencode/tmux-session-state/`. `~/bin/opencode-session-picker` uses that state with tmux pane data to show whether each live OpenCode pane is `working`, `blocked`, `done`, or `error`, then jumps to the selected pane.

_Reference: `private_dot_config/opencode/opencode.jsonc:1`_

## Providers

The built-in OpenAI provider remains the default and uses OAuth subscription auth from `opencode auth login -p openai`. API-key backed `openai-api`, direct OpenCode Zen (`opencode`), and WCS (`wcs`) providers are also allowlisted for explicit model selection. WCS is the private WhoCaresSoftware gateway at `https://ai.whocaressoftware.com/v1`; the live gateway currently exposes the short aliases `gpt`, `deepseek`, `glm`, `kimi`, `qwen`, and `minimax`.

| Model ID | Use Case | Variants |
|---|---|---|
| `openai/gpt-5.5` | Default high-quality fallback, planning, broad research | OAuth provider defaults |
| `openai/gpt-5.4-mini-fast` | Fast bounded tasks, exploration, titles, small model fallback | OAuth provider defaults |
| `openai/gpt-5.4` | Available higher-capacity alternate for explicit selection | OAuth provider defaults |
| `opencode/*` | Selected free OpenCode Zen models via `https://opencode.ai/zen/v1` | Per-model Models.dev metadata |
| `wcs/gpt` | GPT-5.5 through WCS ChatGPT OAuth | `none`, `low`, `medium`, `high`, `xhigh` reasoning effort |
| `wcs/deepseek` | DeepSeek V4 Pro through WCS OpenCode Go | `high`, `max` reasoning effort |
| `wcs/glm` | GLM-5.2 through WCS OpenCode Go | `high`, `max` reasoning effort |
| `wcs/kimi` | Kimi K2.7 Code through WCS OpenCode Go | none; Models.dev lists no reasoning options |
| `wcs/qwen` | Qwen3.7 Max through WCS OpenCode Go | `off`, `on`, `max` thinking; max budget `262144` |
| `wcs/minimax` | MiniMax-M3 through WCS OpenCode Go | `off`, `on` thinking |

Selected direct OpenCode Zen free models: `opencode/big-pickle`, `opencode/deepseek-v4-flash-free`, `opencode/glm-5-free`, `opencode/grok-code`, `opencode/hy3-preview-free`, `opencode/kimi-k2.5-free`, `opencode/ling-2.6-flash-free`, `opencode/mimo-v2.5-free`, `opencode/minimax-m3-free`, `opencode/nemotron-3-ultra-free`, `opencode/north-mini-code-free`, `opencode/qwen3.6-plus-free`, `opencode/ring-2.6-1t-free`, and `opencode/trinity-large-preview-free`.

Commented-out WCS aliases: `deepseek-v4-flash`, `deepseek-v4-pro`, `glm-5.2`, `kimi-k2.7-code`, `qwen3.6-plus`, and `minimax-m3`. They need matching LiteLLM `model_name` routes on the WCS VM before they can be enabled in the client config.

The `-fast` suffix is an actual OAuth-provider model variant. It is used where lower latency matters more than maximum reasoning depth. `enabled_providers` is set to `["openai", "openai-api", "opencode", "wcs"]`; shell aliases `oc-sub` and `oc-oauth` both launch subscription-backed `openai/gpt-5.5`.

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
| `crawl` | subagent | Web archival crawling with crawl4ai into `ai-docs/` | `openai/gpt-5.4-mini-fast`, deny rm/curl/ssh/sudo |
| `librarian` | subagent | External source/GitHub forensics with permalink evidence | Inherits active/default model, read-only, no file writes |
| `web-researcher` | subagent | Web research via DuckDuckGo/webfetch | Inherits active/default model, read-only, no file writes |

Role split: `@scout` is user-invoked for broad reconnaissance, while `librarian` is used for source-backed implementation and change-history analysis.

`web-researcher` defaults to search plus ordinary page fetching/defuddle-style extraction. It escalates to `crawl4ai` only for multi-page crawling, browser-rendered JavaScript content that ordinary extraction cannot read, authenticated/session-based access with user authorization, structured repeated extraction, or persisted archival output such as `ai-docs/`.

`crawl` is an archival agent, not a general reader. Explicit `/crawl <url>` usage means persisted archival intent, even for one URL.

For full/path archival crawls, `crawl` uses Crawl4AI `site_crawler.py --complete` and verifies `site_index.json` for `stats.crawl_complete` plus an empty queued URL count. Default `--max-pages` is a safety chunk; an explicitly supplied `/crawl --max-pages <n>` is treated as a hard cap and reported as incomplete if the boundary still has queued URLs.

Each agent file contains its own description, mode, optional model, temperature, tools, and permissions in YAML frontmatter, plus the prompt body below.

Built-in model selection. `build`, `plan`, `general`, `scout`, and `compaction` inherit the active/default model; only small bounded internal jobs are pinned.

| Agent | Model Selection | Purpose |
|---|---|---|
| `plan` | Inherits active/default model | Planning and no-edit reasoning |
| `general` | Inherits active/default model | Broad subagent work |
| `explore` | `openai/gpt-5.4-mini-fast` | Fast repo exploration |
| `scout` | Inherits active/default model | Manual broad reference/repo scouting |
| `title` | `openai/gpt-5.4-mini-fast` | Session titles |
| `summary` | `openai/gpt-5.4-mini-fast` | Lightweight summaries |
| `compaction` | Inherits active/default model | Conversation compaction |

_Reference: `private_dot_config/opencode/AGENTS.md:1`_

## Custom Commands

| Command | File | Purpose |
|---|---|---|
| `/commit` | `command/commit.md` | Guided git commit (subtask, routes to `@commit`) |
| `/crawl` | `command/crawl.md` | Persist crawl artifacts to `ai-docs/` with crawl4ai (subtask, routes to `@crawl`) |
| `/learn` | `command/learn.md` | Extract AGENTS.md learnings with `openai/gpt-5.4-mini-fast` |
| `/create_plan` | `command/create_plan.md` | Create an implementation plan with `@plan`; inherits active/default model |
| `/research_codebase` | `command/research_codebase.md` | Research the current codebase; inherits active/default model |
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

### writing-great-skills

Shared reference skill for writing and editing Agent Skills with predictable invocation, information hierarchy, pruning, and failure-mode vocabulary.

_Reference: `private_dot_agents/skills/writing-great-skills/SKILL.md`_

### teach

Shared skill for stateful teaching workspaces. It creates mission-grounded lessons, curated resources, learning records, glossaries, and reusable lesson assets in the current workspace.

_Reference: `private_dot_agents/skills/teach/SKILL.md`_

### skill-creator

OpenCode-only operational skill for creating, improving, and validating Agent Skills. Its `SKILL.md` is a compact branch router for create, improve, evaluate, description-optimization, and blind-comparison work; detailed eval and description mechanics live in `references/`.

Key bundled resources:

- `references/evaluation-loop.md` -- eval workspace layout, Task subagent run pattern, grading, benchmark aggregation, and review viewer generation
- `references/description-optimization.md` -- invocation-mode decisions and manual description rewrite loop
- `eval-viewer/generate_review.py` -- static HTML review UI for human feedback on eval outputs

_Reference: `private_dot_config/opencode/skills/skill-creator/SKILL.md`_

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
- `evals/evals.json` -- Routing evals for defuddle/web-researcher/crawl4ai boundaries, archival intent, exhaustive site crawls, schema extraction, and JavaScript-rendered fallback

Ordinary single-page reading, summarization, or markdown extraction should use `defuddle`. Use `crawl4ai` for single pages only when JavaScript-heavy rendering defeats `defuddle`, or when the task needs crawling, sessions, structured extraction, or repeatable scraping.

`site_crawler.py` supports `--complete` for resume-until-empty bounded crawls, `--max-total-pages` for hard caps, and a headless default with `--visible` for debugging. `basic_crawler.py`, `batch_crawler.py`, and `extraction_pipeline.py` accept explicit output directories so artifacts do not leak into the caller's working directory.

Skill eval workspaces such as `crawl4ai-workspace/` are source-only and ignored by chezmoi so review HTML, benchmark JSON, and run outputs are not deployed as live OpenCode skills.

Loaded by agents via `skill({ name: "crawl4ai" })`.

_Reference: `private_dot_config/opencode/skill/crawl4ai/SKILL.md`_

## Gotchas

- Agent markdown files use YAML frontmatter delimiters (`---`); syntax must be exact.
- Model IDs must match the provider's exact format (e.g., `amazon-bedrock/anthropic.claude-opus-4-5-...`).
- Granular bash patterns in YAML frontmatter work correctly (confirmed via OpenCode source).
- `package.json` and `bun.lock` under `.config/opencode/` are repo-ignored artifacts and should stay in `.chezmoiignore`.
- OpenCode loads config-time plugin changes only when a new OpenCode process starts; restart existing panes after changing `plugins/*.js`.

_Reference: `private_dot_config/opencode/README.md:131`_

## References

- Main config: `private_dot_config/opencode/opencode.jsonc:1`
- README: `private_dot_config/opencode/README.md:1`
- AGENTS: `private_dot_config/opencode/AGENTS.md:1`
