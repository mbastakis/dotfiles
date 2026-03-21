# System Overview

How the chezmoi source tree maps to the target filesystem, what gets deployed, and what stays source-only.

## Component Interaction Model

```mermaid
flowchart LR
  K[Karabiner] --> G[Ghostty]
  G --> T[tmux]
  G --> Z[zsh]
  T --> Z
  Z --> N[Neovim]
  Z --> M[Mail Stack\nNeoMutt + mbsync + msmtp + notmuch + abook]
  Z --> O[OpenCode CLI]
  C[chezmoi lifecycle] --> Z
  C --> N
  C --> M
  C --> O
  C --> K
  C --> G
  C --> T
```

Input flows from the physical keyboard through Karabiner (home row mods, hyper key), into Ghostty (terminal keybindings), then into tmux (prefix commands) or directly to zsh (shell keybindings). From zsh, input reaches Neovim, OpenCode, and NeoMutt. Chezmoi manages configuration for all layers, including the mail stack and its launchd automation.

## Source-to-Target Mapping

Chezmoi translates source-state file names to target paths using naming conventions (`private_`, `dot_`, `encrypted_`, `.tmpl`).

| Source (chezmoi) | Target | Notes |
|---|---|---|
| `.chezmoi.toml.tmpl` | `~/.config/chezmoi/chezmoi.toml` | Config, profile selection, encryption settings |
| `key.txt.age` | _(source-only)_ | Passphrase-encrypted age private key |
| `bin/chezmoi-bws` | _(source-only)_ | BWS token wrapper script |
| `literal_bin/` | `~/bin/` | Shell utility scripts |
| `private_dot_ssh/` | `~/.ssh/` | SSH keys (encrypted) |
| `private_dot_config/` | `~/.config/` | Application configs |
| `private_dot_config/isyncrc.tmpl` | `~/.config/isyncrc` | mbsync/isync config |
| `private_dot_config/msmtp/private_config.tmpl` | `~/.config/msmtp/config` | SMTP account config |
| `private_dot_config/notmuch/default/config.tmpl` | `~/.config/notmuch/default/config` | notmuch profile config |
| `private_dot_config/notmuch/default/hooks/executable_post-new.tmpl` | `~/.config/notmuch/default/hooks/post-new` | post-index account/folder tagging |
| `private_dot_config/neomutt/` | `~/.config/neomutt/` | NeoMutt entrypoint, includes, mailcap |
| `private_dot_abook/` | `~/.abook/` | Abook contact config and data |
| `private_Library/LaunchAgents/com.mbastakis.mail-sync.plist.tmpl` | `~/Library/LaunchAgents/com.mbastakis.mail-sync.plist` | Mail sync scheduler |
| `literal_bin/executable_mail-*` | `~/bin/mail-*` | Mail helper scripts (`mail-sync`, `mail-open`) |
| `.chezmoiscripts/` | _(lifecycle scripts)_ | Before/after scripts (e.g. LaunchAgent reload, Ghostty-only Cmd+H override), not deployed |
| `.chezmoidata.yaml` | _(template data)_ | Catppuccin Mocha color palette |
| `dot_zshrc` | `~/.zshrc` | Zsh entry point |
| `dot_zsh/` | `~/.zsh/` | Zsh module files |

_Reference: `AGENTS.md:78`_

## Source-Only Directories

These directories exist in the repo but are never deployed to the target filesystem:

| Directory | Purpose |
|---|---|
| `ai-docs/` | Crawled documentation for AI agents |
| `code-portable-data/` | VS Code portable data |
| `bin/chezmoi-bws` | BWS helper (used during template rendering only) |
| `docs/` | This documentation tree |

_Reference: `.chezmoiignore:11`_

## Ignored Artifacts

The `.chezmoiignore` file uses **target-state paths** (not source-state names) and supports chezmoi template conditionals:

- **Build artifacts:** `node_modules/`, `target/`, `__pycache__/`, lock files
- **Caches:** `.cache/`, `.config/carapace/.versions`, `lazy-lock.json`, yazi plugins
- **Runtime state:** `glab-cli/recover/`, `.obsidian/`, `.DS_Store`
- **Obsidian vault generated files:** Plugin binaries (`main.js`, `manifest.json`, `styles.css`), themes, icons, and `workspace.json` under `Documents/notes/.obsidian/` are ignored — only settings JSONs and plugin `data.json` files are managed
- **Profile-conditional:** DT work configs (glab, git work config, GitLab SSH keys) excluded when profile is not `dt-work`
- **OS-conditional:** macOS-only configs (Aerospace, Karabiner, Finicky, SketchyBar, Ghostty LaunchAgent, mail LaunchAgent) excluded on Linux

_Reference: `.chezmoiignore:19`, `.chezmoiignore:54`_

## Profile System

The config template (`.chezmoi.toml.tmpl`) determines the active profile at `chezmoi init` time:

1. Check `CHEZMOI_PROFILE` env var (`dt-work`, `work`, or `personal`).
2. If unset, prompt interactively via `promptChoiceOnce`.
3. Profile sets `.profile` and `.dtWork` template variables.
4. These variables control conditional ignores, template rendering, and secret fetching.

_Reference: `.chezmoi.toml.tmpl:1`_

## Encryption Model

A single age keypair protects all sensitive files. The passphrase is only needed once during `chezmoi init`:

```mermaid
flowchart TD
  A[key.txt.age<br/>in repo, passphrase-encrypted] -->|decrypted once by script 00| B[~/.config/chezmoi/key.txt<br/>plaintext identity]
  B -->|age decrypt| C[~/.ssh/id_ed25519]
  B -->|age decrypt| D[~/.supermaven/config.json]
  B -->|age decrypt| E[~/.local/share/bws/token]
  E -->|chezmoi-bws wrapper| F[Bitwarden Secrets Manager]
  F -->|bitwardenSecrets template func| G[API keys in ~/.zsh/local.zsh]
```

_Reference: `AGENTS.md:62`_

## References

- Root AGENTS: `AGENTS.md:78` (key paths table)
- Chezmoi config template: `.chezmoi.toml.tmpl:1`
- Ignore rules: `.chezmoiignore:1`
- Encryption section: `AGENTS.md:62`
