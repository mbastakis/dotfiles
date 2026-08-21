# OpenCode V2

Use this page instead of upstream OpenCode examples when the active host is OpenCode V2. The bundled upstream Worktrunk references currently describe the stable V1 CLI and plugin API.

## Detect the host

```bash
command -v opencode2
opencode2 --version
opencode2 service status
```

Use `opencode2` when it is the configured host. Do not replace it with the V1 `opencode` binary, an interactive shell alias, or an `opencode-launch` wrapper in automation.

## Worktrunk commit generation

`wt merge`, `wt step commit`, and `wt step squash` pipe a rendered prompt to `commit.generation.command` on stdin and expect a plain commit message on stdout. The prompt can contain full diffs, filenames, branch names, recent commits, and approved project guidance, so generation sends repository data to the configured external model.

On this workstation, use the background-service-connected V2 CLI with the dedicated agent at `~/.config/opencode/agents/worktrunk-commit.md`:

```toml
# ~/.config/worktrunk/config.toml
[commit.generation]
command = "cd \"$HOME\" && opencode2 run --agent worktrunk-commit --model wcs/gpt-5.6-luna#low --title worktrunk-commit"
```

Why this form:

- `cd "$HOME"` keeps repository-local OpenCode config, agents, instructions, and plugins out of the generator's configuration search.
- `opencode2 run` reads a piped prompt and prints the response.
- The background service owns provider credentials and global configuration.
- `--model` pins the selected session model; a primary agent's configured model alone does not change an existing session selection.
- `--title` prevents automatic title generation from sending prompt metadata to the title agent.
- The dedicated `worktrunk-commit` primary agent denies every tool and returns only a commit message.
- Do not select the interactive `commit` subagent, which plans, stages, and commits files itself.

Do not use:

```text
opencode run ...                  # V1 binary
oc ...                            # interactive shell alias
opencode2 run --standalone ...    # bypasses the configured service environment
opencode2 run --agent commit ...  # performs a different workflow
opencode2 run --format json ...   # Worktrunk expects plain text
opencode2 run from the repo       # loads repository-local agents/plugins
```

### First-run Claude prompt

A prompt such as:

```text
Configure claude for commit messages? [y/N/?]
```

is Worktrunk's core first-run commit-generation setup, not a hook. Worktrunk v0.74 checks executables in this order:

```text
claude -> codex -> opencode
```

It does not detect `opencode2`. If `claude` exists and no command is configured, the prompt therefore offers Claude. Add `[commit.generation]` explicitly rather than accepting the wrong auto-detected tool.

Verify without committing:

```bash
wt config show --full
wt step commit --dry-run
```

Both commands call the model, may incur cost, transmit repository data, and create a durable session in the shared OpenCode service. Use them only when a representative diff exists and those side effects are acceptable. Plain `wt config show` validates loading without a model call.

## Switching and session location

OpenCode shell commands run in child processes. Even with Worktrunk shell integration installed, `wt switch` inside a tool call cannot change the persistent OpenCode session's working directory. Run subsequent tools with the target worktree as their working directory or start a new handoff there. For the user's own interactive shell, `wt config show` must report shell integration configured before `wt switch` can change the parent shell.

## Agent Handoffs

Use `opencode2 run` as the executed agent command:

```bash
wt switch --create <branch> -x 'opencode2 run' -- '<task>'
```

For a detached multiplexer session:

```bash
tmux new-session -d -s <branch> \
  "wt switch --create <branch> -x 'opencode2 run' -- '<task>'"
```

The user must explicitly request the handoff. Under OpenCode V2, authorization comes from the user's prompt or `AGENTS.md`, not an otherwise ignored `CLAUDE.md`. Verify that the tmux/Zellij child remains alive after launch. Do not launch parallel sessions for ordinary worktree creation.

## Activity tracking plugin

Worktrunk's command:

```bash
wt config plugins opencode install
```

installs a plugin written for the stable V1 factory API. OpenCode V2 plugins use the `/v2` API with a plugin `id` and `setup` or `effect` entrypoint. Treat the upstream installer as V1-only until Worktrunk ships V2 support; do not install or overwrite a V2 plugin with it.

Activity tracking is optional. Its absence does not affect worktree creation, merge behavior, or commit-message generation. When implementing V2 tracking, verify the current OpenCode V2 plugin docs and API before editing `~/.config/opencode/plugins/`.

## Failed merge against a dirty target

A failed `wt merge` may already have committed or squashed the source branch before Worktrunk checks whether the target worktree can accept the push. An error such as:

```text
Can't push to local main branch: conflicting uncommitted changes
```

means the source commit is preserved. Inspect both worktrees with:

```bash
git worktree list --porcelain
wt list --full --branches
git show --stat <source-commit>
```

Do not rerun the merge or remove the source worktree. Reconcile the source commit with the target's dirty files, validate the combined target state, then commit the target work before cleaning up the source branch.

## Capability limits

OpenCode does not expose Claude Code's WorktreeCreate/WorktreeRemove lifecycle hooks. Create and remove Worktrunk worktrees explicitly:

```bash
wt switch --create <branch>
wt remove <branch>
```

Do not use Claude-only `/wt-switch-create` or `isolation: "worktree"` guidance in OpenCode.
