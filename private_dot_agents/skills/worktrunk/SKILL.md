---
name: worktrunk
description: "Worktrunk (`wt`) workflows for Git worktrees. Use when the user mentions Worktrunk or `wt`; creates, switches, lists, merges, removes, or repairs worktrees; edits `.config/wt.toml` or `~/.config/worktrunk/config.toml`; configures hooks, aliases, LLM commit messages, or agent handoffs; or troubleshoots shell integration, approvals, and OpenCode integration."
license: MIT OR Apache-2.0
compatibility: Requires the `wt` CLI (https://worktrunk.dev)
---

# Worktrunk

Worktrunk is the control plane for Git worktrees. Use `wt` rather than assembling equivalent `git worktree` commands unless diagnosing Worktrunk itself.

## Operating Workflow

1. **Classify** - Identify which branches the request spans: worktree lifecycle, configuration, hooks, commit generation, shell integration, or agent integration. Read only the matching files under `reference/`; for OpenCode, read `reference/opencode-v2.md` before following upstream OpenCode examples. _Done when every requested behavior maps to an authoritative reference._
2. **Inspect** - Run `wt --version`, `wt config show`, `git status --short --branch`, and the relevant `wt <command> --help`. Inspect `.config/wt.toml` when present; identify a merge target only for lifecycle operations that need one. _Done when the current worktree, effective config, and commands that may mutate state are known._
3. **Plan trust boundaries** - Separate user config from project config. User config is personal and uncommitted; propose durable preference changes before editing it. Project hooks, aliases, and `commit.generation.template-append` are repository-supplied input; never approve them for the user. _Done when every requested change has an owner and every approval remains a human decision._
4. **Execute narrowly** - Use the smallest `wt` command or config edit that satisfies the request. Preserve existing TOML structure and comments. Do not add compatibility paths unless an installed version requires them. _Done when the command or edit succeeds without unrelated worktree changes._
5. **Verify** - Re-run a narrow local status command such as `wt list`, `wt config show`, or `wt hook show`. `wt config show --full` and `wt step commit --dry-run` call the configured model; use them only when the user has accepted outbound diff/config data, cost, and a durable OpenCode session. For handoffs, verify the multiplexer child is still alive. _Done when Worktrunk reports the intended effective state, Git status is understood, and any spawned process is confirmed._

## Reference Map

- CLI overview and installation: `reference/worktrunk.md`
- Create or switch worktrees: `reference/switch.md`
- List worktrees and status: `reference/list.md`
- Merge and clean up: `reference/merge.md`
- Remove worktrees: `reference/remove.md`
- Commit, squash, copy ignored files, and `for-each`: `reference/step.md`
- User and project configuration: `reference/config.md`
- Hooks and template variables: `reference/hook.md`
- Aliases and pipelines: `reference/extending.md`
- LLM commit messages: `reference/llm-commits.md`
- Shell integration failures: `reference/shell-integration.md`
- Common failures: `reference/troubleshooting.md`
- Frequently asked questions and edge cases: `reference/faq.md`
- macOS code-signing verification: `reference/code-signing.md`
- OpenCode V2 commands, commit generation, and integration limits: `reference/opencode-v2.md`
- Agent integration capability matrix: `reference/claude-code.md`
- Recipes and parallel-agent patterns: `reference/tips-patterns.md`

The bundled upstream references were imported from `max-sixty/worktrunk` commit `9c37aae5b9af7e5a38306479b2453c919ea7b99c`. They may mention `CLAUDE.md`, `opencode`, or Claude-only lifecycle features; under OpenCode V2, `reference/opencode-v2.md` overrides those host-specific examples. For version-sensitive behavior, compare `wt --version` and command help before trusting examples.

## Configuration Ownership

**User config**: `~/.config/worktrunk/config.toml`

Use for personal worktree paths, command defaults, aliases, hooks, and the external command used for commit generation. It is not committed. Preserve comments and request consent before changing preferences unless the user explicitly asked for the change.

**Project config**: `<repo>/.config/wt.toml`

Use for repository-wide hooks, aliases, dev-server URLs, and shared commit-message guidance. It is committed and may contain arbitrary shell code.

## Hook Approvals

Worktrunk blocks unapproved project hooks and aliases because they execute repository-supplied shell commands. Project `commit.generation.template-append` is also approval-gated because it is sent to the configured model. If a non-interactive command says approval is required:

- Stop and show the user the blocked commands.
- Ask the user to run `wt config approvals add` interactively.
- Never run `wt config approvals add --yes` or add `--yes` merely to bypass the trust gate.

CI or a controlled container may use `--yes` only when its operator already owns and audits the project config.

## Destructive Operations

Before `wt merge` or `wt remove`, inspect the current branch, uncommitted changes, merge target, and configured defaults. These commands can commit changes, rewrite branch history through squash or rebase, delete a branch, and remove a worktree.

`wt merge` can commit or squash the source branch before discovering that the target worktree is dirty. If it then reports `conflicting uncommitted changes`, do not rerun blindly: the new commit remains on the source branch. Compare the source commit with the target's dirty files, preserve a temporary snapshot outside the target index when reconciling, apply the resolved delta to the target without staging it, run repository validation, and keep the source worktree until the target changes are committed.

Do not substitute raw `git worktree remove`, manual directory deletion, or force flags unless the user explicitly needs recovery and the relevant Worktrunk command cannot handle it.

## Switching Location

`wt switch` needs shell integration to change an interactive parent shell. If `wt config show` reports shell integration missing, fix that before promising directory switching. A `wt switch` executed through an agent's shell tool only changes that child process; it does not move the persistent OpenCode session into the selected worktree. For agent work, launch the command in the target worktree or start a new handoff there.

## Agent Handoffs

Use a handoff only when the user explicitly asks to spawn or delegate work and a supported terminal multiplexer is active. Use the CLI for the current host:

- OpenCode V2: `opencode2 run`
- OpenCode V1: `opencode run`
- Claude Code: `claude`

```bash
# tmux
tmux new-session -d -s <branch-name> \
  "wt switch --create <branch-name> -x '<agent-cli>' -- '<task description>'"

# Zellij
zellij run -- wt switch --create <branch-name> \
  -x '<agent-cli>' -- '<task description>'
```

The user's OpenCode V2 project instructions (`AGENTS.md`) or an explicit prompt must authorize the pattern. `CLAUDE.md` is authorization only when the active host actually loads it. Do not use handoffs for ordinary worktree creation.
