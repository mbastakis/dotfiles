# Architecture

How `chezmoi apply` turns this source tree into a working machine: script ordering, the encryption chain, unified configuration, and the gotchas that are not obvious from reading any single file. For the file-by-file inventory, read the source tree itself — `chezmoi managed` and `.chezmoiscripts/` are authoritative.

## Component Interaction Model

```mermaid
flowchart LR
  K[Karabiner] --> G[Ghostty] --> T[tmux] --> Z[zsh]
  G --> Z
  Z --> N[Neovim]
  Z --> M[Mail stack]
  Z --> O[OpenCode]
  B[credential bridge :4098<br/>Atlas capability required] --> OB[opencode2 service :4097]
  TS[Tailscale Serve<br/>Atlas-only ingress] --> B
  C[chezmoi lifecycle] -.manages.-> K & G & T & Z & N & M & O & OB & B
```

Keyboard input flows Karabiner → Ghostty → tmux → zsh, and from zsh into Neovim, the mail stack, and OpenCode. Atlas Traefik applies Authentik forward-auth, then reaches the designated Mac through an Atlas-only Tailscale Serve route and a loopback credential bridge. Chezmoi manages the Mac layers; authoritative identity, network topology, and remote-host runbooks live in the sibling Kavouki repository.

## Apply Phases

```mermaid
flowchart TD
  A[Compute target state] --> B[Before scripts]
  B --> C[File operations<br/>decrypt encrypted_, render .tmpl, deploy]
  C --> D[After scripts]

  B --> B1[00 decrypt age key → 01 install bws → 02 brew bundle]
  D --> D1[03–04 tool caches and extensions<br/>bat, Yazi, gh]
  D1 --> D2[07 mail runtime dirs]
  D2 --> D4[10 OpenCode remote reconcile<br/>designated Mac only]
  D --> D6[macOS settings migration + reconcile]
```

Scripts run alphabetically within each phase, so the numeric prefixes are the ordering mechanism. The before phase exists to satisfy file operations: the age identity must exist before `encrypted_` files can decrypt, and the `bws` CLI must exist before `bitwardenSecrets` template calls can render.

Almost everything is `run_onchange`, triggered by `sha256sum` hashes of the inputs each script owns. The OpenCode hook hashes the LaunchAgents, controller, credential bridge, and provider environment; the opencode2 service hot-reloads config, agents, commands, and skills itself, so those no longer trigger reconciliation. When writing a new `run_onchange` script, embed only deterministic inputs the operation owns — never dates or unrelated aggregates.

## Fresh-Machine Bootstrap

A fresh machine has a chicken-and-egg problem: templates that call `bitwardenSecrets` need the BWS token, but that token is itself an age-encrypted managed file. Break the cycle by deploying the token first; the configured `scripts/bws-auth` wrapper reads it only for each `bws` invocation, so the token is not exported to every shell descendant:

```bash
chezmoi apply --force "$HOME/.local/share/bws/token"
chezmoi apply --force
```

The age passphrase is needed exactly once: the `00` before-script decrypts `key.txt.age` into `~/.config/chezmoi/key.txt` via a mode-restricted temp file and atomic rename, so a failed decryption never clobbers a working identity. On a machine without Homebrew, the `02` script installs it, and in non-interactive shells it skips Mac App Store installs by deriving `mas` IDs from the Brewfile itself rather than maintaining a second list.

## Encryption Model

One age keypair protects every secret; everything downstream is derived without further prompts:

```mermaid
flowchart TD
  A[key.txt.age<br/>in repo, passphrase-encrypted] -->|before-script 00| B[~/.config/chezmoi/key.txt]
  B -->|age decrypt during file ops| C[~/.ssh keys · ~/.supermaven/config.json · atuin key]
  B -->|age decrypt| E[~/.local/share/bws/token]
  E -->|scripts/bws-auth wrapper| F[bws CLI]
  F --> H[Bitwarden Secrets Manager]
  H -->|bitwardenSecrets template func| G[API keys rendered into<br/>~/.config/zsh/exports.zsh]
```

The chain spans five files: `key.txt.age`, `.chezmoiscripts/run_onchange_before_00-decrypt-private-key.sh.tmpl`, the encrypted token at `private_dot_local/private_share/private_bws/encrypted_private_token.age`, `scripts/bws-auth` (the scoped token reader), and `.chezmoi.toml.tmpl` (identity/recipient plus the wrapper-backed `bitwardenSecrets` command). Breaking any link breaks template rendering repo-wide.

## Runtime-Owned Files

Some managed files are bootstrap seeds: chezmoi deploys them once, then defers to the CLI that rewrites them at runtime.

- Kubeconfigs (`~/.config/kube/config-*`) — `kubectl`, `aws`, and `kind` rewrite contexts and serialization.
- `~/.local/share/colima/default/colima.yaml` — Colima rewrites generated formatting.
- `~/.config/glab-cli/config.yml` — glab stores auth fields and update timestamps in place.

`textconv` rules in `.chezmoi.toml.tmpl` normalize these so `chezmoi diff` shows semantic changes instead of re-serialization noise. Note that `textconv` patterns match **absolute target paths**, not the relative paths shown in diff headers.

## Unified Configuration

Personal and work settings share one target state. There is no profile selector or profile-scoped rendering: work configuration is always deployed, while Git and Jujutsu identities remain scoped by remote URL or repository path where appropriate.

If Tailscale, Harmony, macOS, or an operator flips DNS or proxy state on the `AX88179A` Ethernet service, run the `reset_work_network` zsh function (defined in `private_dot_config/zsh/functions.zsh`) to disable Tailscale DNS and the HTTP/HTTPS proxies again. This is a manual repair command; the lifecycle no longer applies network policy itself.

## Ignored Artifacts

`.chezmoiignore` matches **target-state paths** (`.config/foo`, never `private_dot_config/foo`) and is rendered as a template. This repository intentionally targets macOS only, so OS-specific template guards and fallback branches are unnecessary. The non-obvious entries:

- Any repo-only directory (`docs/`, `ai-docs/`, `tests/`) must be listed or chezmoi deploys it into `~/`.
- Obsidian: only volatile state (`workspace.json`, caches, auto-downloaded plugin code) is ignored — settings JSONs and plugin `data.json` files stay managed.
- Karabiner: the build system (`build.sh`, `src/`) stays source-only; only the generated `karabiner.json` deploys.
- Work configuration is always in the target state. The OpenCode backend and credential-bridge stack remain hostname-scoped and deploy only to the designated Mac.

## Operational Notes

- `scripts/bws-auth` reads the age-decrypted token for each `bws` invocation; ordinary shells and their child processes do not inherit `BWS_ACCESS_TOKEN`.
- Step `10` pushes provider credentials into the opencode2 service environment, reloads the LaunchAgents, and converges the stack. The service hot-reloads config/agents/commands/skills; `opencode2 service restart` is only needed for binary updates, and clients reconnect and resume their sessions afterward.
- A missing data key in a `.chezmoiignore` template conditional breaks unrelated commands (`add`, `status`, `apply`) — keep templates compatible with existing keys until `chezmoi init` has run everywhere.
- Use `chezmoi apply --dry-run --force` for non-interactive validation; without `--force`, changed files trigger TTY prompts that fail headless.
- Source location is not assumed: templates resolve the checkout through `.chezmoi.sourceDir`, persisted as `sourceDir` in the rendered config.
