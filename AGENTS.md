# Dotfiles (chezmoi)

## Install

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply mbastakis
```

## Commands

```bash
chezmoi apply              # Apply source → target (daily use)
chezmoi apply --dry-run    # Preview changes without applying
chezmoi diff               # Show diff between source and target
chezmoi update             # Git pull + apply
chezmoi init               # Regenerate config (after .chezmoi.toml.tmpl changes)
chezmoi add --encrypt FILE # Add file to source as encrypted
chezmoi managed            # List all managed files
chezmoi ignored            # List all ignored files
chezmoi forget FILE        # Stop managing a file
```

### aws-login repositories

`mr checkout` in `~/dev/personal/dev-tools` clones:

- `git@github.com:mbastakis/aws-login.git`
- `git@github.com:mbastakis/homebrew-tap.git`

### Pre-commit hooks

```bash
mise exec -- task check     # Run repository validation hooks and tests
pre-commit run --all-files  # Run all hooks
pre-commit run shellcheck   # Shellcheck only
pre-commit run gitleaks     # Secrets detection only
```

Hooks: shellcheck (`-x -e SC1091`), gitleaks, yamllint (relaxed), trailing-whitespace,
end-of-file-fixer, check-yaml/toml/json, detect-private-key (excludes `.age`), and large files (500KB).
Pre-push: `chezmoi apply --dry-run --force`.

## Apply Order

```
1. Read source + destination state
2. Compute target state (templates, encrypted files)
3. Before scripts (alphabetical):
   00-decrypt-private-key  → atomically installs the age identity when key.txt.age changes
   01-install-bws          → installs the pinned bws CLI version (run_onchange)
   02-install-packages     → stages Homebrew trust and runs brew bundle (run_onchange)
4. File operations (alphabetical by target):
   - Decrypt encrypted_ files (age identity, no prompt)
   - Render .tmpl templates (bitwardenSecrets → bws CLI using BWS_ACCESS_TOKEN)
   - Deploy files, directories, symlinks
5. After scripts (alphabetical):
   03-bat-cache            → rebuilds the bat theme cache (run_onchange)
   03-yazi-packages        → installs declared Yazi packages (run_onchange)
   04-install-gh-extensions → installs pinned gh extensions (run_onchange)
   06-runtime-dirs         → creates shell-configured runtime directories and enforces GnuPG permissions
   07-mail-runtime-dirs    → creates shared and per-account mail directories (run_onchange)

   10-opencode-remote      → removes retired OpenCode proxy artifacts, then reconciles backend + credential bridge + Tailscale Serve (run_onchange)
   macos-settings-migration → removes retired global Ghostty shortcuts (run_once)
   macos-settings           → invokes the reusable macOS defaults command (run_onchange)
```

## Encryption

Single age keypair, passphrase-protected. Passphrase only needed on first `chezmoi init`.

```
key.txt.age (in repo, passphrase-encrypted)
    ↓ decrypted once by run_onchange_before_00
~/.config/chezmoi/key.txt (plaintext identity)
    ↓ used by chezmoi builtin age (no further prompts)
    ├── ~/.ssh/id_ed25519
    ├── ~/.supermaven/config.json
    └── ~/.local/share/bws/token → scripts/bws-auth scopes BWS_ACCESS_TOKEN to bws
                                      └── bws renders API keys into ~/.config/zsh/exports.zsh
```

## Key Paths

| Source (chezmoi)                                                | Target                               | Notes                                                                |
| --------------------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------- |
| `.chezmoi.toml.tmpl`                                            | `~/.config/chezmoi/chezmoi.toml`     | Config and encryption                                                |
| `key.txt.age`                                                   | _(ignored, source-only)_             | Passphrase-encrypted age key                                         |
| `mise.toml`                                                     | _(ignored, source-only)_             | Repo-local Node, go-task, pre-commit, ShellCheck, and yamllint tools  |
| `Taskfile.yml`                                                  | _(ignored, source-only)_             | go-task runner for dotfiles workflows                                |
| `.pre-commit-config.yaml`                                       | _(ignored, source-only)_             | Repo-local hooks                                                     |
| `private_dot_agents/skills/`                                    | `~/.agents/skills/`                  | Shared harness-agnostic Agent Skills for OpenCode                    |
| `dev/personal/dev-tools/dot_mrconfig`                           | `~/dev/personal/dev-tools/.mrconfig` | Personal dev-tools workspace repos                                   |
| `literal_bin/`                                                  | `~/bin/`                             | Shell utility scripts                                                |
| `private_dot_ssh/`                                              | `~/.ssh/`                            | SSH keys (encrypted) and host aliases                                |
| `private_dot_config/`                                           | `~/.config/`                         | App configs                                                          |
| `private_dot_config/abook/`                                     | `~/.config/abook/`                   | Abook config                                                         |
| `private_dot_config/vicinae/`                                   | `~/.config/vicinae/`                 | Fully managed Vicinae settings                                      |
| `private_dot_config/zsh/`                                       | `~/.config/zsh/`                     | Zsh config via `ZDOTDIR`                                             |
| `private_dot_local/private_share/abook/`                        | `~/.local/share/abook/`              | Abook data                                                           |
| `private_dot_local/private_share/colima/`                       | `~/.local/share/colima/`             | Colima config + state                                                |
| `private_dot_local/private_share/vicinae/`                      | `~/.local/share/vicinae/`            | Managed Vicinae themes, scripts, and extensions                      |
| `.chezmoiscripts/`                                              | _(lifecycle scripts, not deployed)_  | Before/after scripts                                                 |
| `.chezmoidata.yaml`                                             | _(template data)_                    | Colors plus mail, Taskwarrior, and OpenCode host settings            |

## .chezmoiignore

Uses **target-state paths** (not source-state):

- Correct: `.config/foo/bar`
- Wrong: `private_dot_config/foo/bar`

### Operational Gotchas

- `.chezmoiignore` is rendered as a template for many commands (`add`, `status`, `apply`); missing data keys in conditions can break unrelated commands.
- When removing data keys from `.chezmoi.toml.tmpl`, remove all template and ignore consumers in the same change; existing rendered configs may retain unused keys until `chezmoi init` regenerates them.
- For non-interactive checks, prefer `chezmoi apply --dry-run --force`; without `--force`, changed files may trigger TTY prompts and fail in headless shells.
- In this repo, `chezmoi diff` is most reliable with absolute target paths (for example `/Users/mbastakis/.config/git/config`) when diffing a single file.
- `Documents/notes/.obsidian/workspace.json` is volatile UI state (recent files/workspace layout) and should stay ignored to avoid noisy churn and accidental overwrite.
- `glab` can write auth fields and `last_update_check_timestamp` in `.config/glab-cli/config.yml`; the modify template treats it as a bootstrap seed and preserves an existing live file.
- Chezmoi `textconv` patterns match absolute target paths, not the relative paths displayed in `chezmoi diff` headers.
- Kubeconfig and Colima files are bootstrap seeds after first creation; existing live files are preserved because `kubectl`, `aws`, `kind`, and Colima rewrite runtime state.
- Any new repo-only directory (like `docs/`) must be added to `.chezmoiignore` or chezmoi will deploy it to `~/`. The ignore file uses target-state paths, so `docs/` not `literal_docs/`.
- External infrastructure automation belongs in the sibling Kavouki repository, not this chezmoi source.
- OpenCode `reconcile` and `start` must not replace healthy backend or proxy
  processes. Apply pending desired generations only with explicit `restart
  server|proxy|all`.

## Shell Script Conventions

### Every bash script must have

```bash
#!/bin/bash
set -euo pipefail
```

### Error handling

- **Fail-fast**: `set -euo pipefail` — no silent failures
- **Graceful degradation**: `command || true` for non-critical operations
- **Command guards**: `command -v tool &>/dev/null` before using optional tools
- **Exit code capture**: `set +e; output=$(...); rc=$?; set -e`

### Quoting and variables

- Always double-quote variables: `"$variable"`, `"${variable:-default}"`
- Default values: `"${1:-}"`, `"${BWS_ACCESS_TOKEN:-}"`
- Arrays: `"${cmd[@]}"`, `"${args[@]}"`
- Heredocs for multi-line messages: `cat >&2 <<EOF ... EOF`

### Logging

- Colored helpers: `log_info()`, `log_error()`, `log_warning()` with ANSI codes
- Errors to stderr: `echo "Error: ..." >&2`

### Argument parsing

```bash
while [[ $# -gt 0 ]]; do
    case "$1" in
        --flag) FLAG=true; shift ;;
        --) shift; break ;;
        *) args+=("$1"); shift ;;
    esac
done
```

## Chezmoi Template Conventions

### Change detection (run_onchange scripts)

```
# hash: {{ include "path/to/file" | sha256sum }}
```

### Template functions used

| Function                            | Purpose                                |
| ----------------------------------- | -------------------------------------- |
| `{{ .chezmoi.sourceDir }}`          | Chezmoi source directory path          |
| `{{ .email }}`, `{{ .name }}`       | User data from config                  |
| `{{ bitwardenSecrets "uuid" }}`     | Fetch secret from BWS                  |
| `{{ include "file" \| sha256sum }}` | File content hash for change detection |
| `{{ value \| quote }}`              | Quote for TOML output                  |
| `{{ value \| trim }}`               | Trim whitespace from secrets           |

### Whitespace control

Always use `{{-` and `-}}` to trim surrounding whitespace in template tags.

## Neovim Config (private_dot_config/nvim/)

- **2-space indent**, double quotes, trailing commas
- Plugin specs: `return { "author/plugin", opts = { ... } }` (lazy.nvim)
- Keymaps: `vim.keymap.set("n", "<leader>key", func, { desc = "Category: Action" })`
- LSP configs: `after/lsp/<server>.lua` with `vim.lsp.config()`
- Formatter: stylua. Linter: selene (permissive, `std = "lua51"`)

## Zsh Config (private_dot_config/zsh/)

`dot_zshenv.tmpl` still renders to `~/.zshenv`; interactive/login zsh config lives in `private_dot_config/zsh/` and is loaded via `ZDOTDIR=~/.config/zsh`.

Load order: exports → plugins → completions → tools → aliases → functions →
fzf → fzf-tab → keybindings

- Conditional sourcing: `[[ -f "$file" ]] && source "$file"`
- Tool init: `command -v tool &>/dev/null && eval "$(tool init zsh)"`
- Startup caching: `[[ ! -f "$cache" ]] || [[ "$bin" -nt "$cache" ]]`
- ZLE widgets: define function → `zle -N name` → `bindkey '^X' name`

## Karabiner (private_dot_config/private_karabiner/)

Build system only — `karabiner.json` is generated, never edit directly.
Only `karabiner.json` is deployed to target; `build.sh` and `src/` stay in source.

```bash
# Rebuild from any directory:
"$(chezmoi source-path)"/private_dot_config/private_karabiner/build.sh
```

## Documentation (`docs/`)

Docsify site deployed to GitHub Pages at `https://mbastakis.github.io/dotfiles/`.
Source lives in `docs/`; served as a zero-build SPA via `docs/index.html`.

### Docs Maintenance Rule

Docs hold only insight the code can't express: cross-tool aggregations, design rationale, runbooks. They never enumerate what the code already lists (packages, plugins, aliases, options, routes) — inventory changes never require a doc edit. Cite source files by path only, never by line number.

Update a doc only when its insight changes:

| Change                                                         | Doc to update             |
| -------------------------------------------------------------- | ------------------------- |
| Any custom keymap/keybinding (Karabiner, Ghostty, tmux, zsh, NeoMutt, Neovim) | `docs/shortcuts.md`       |
| Chezmoi lifecycle behavior, encryption/secrets flow, bootstrap procedure       | `docs/architecture.md`    |
| Email stack procedures or troubleshooting                                     | `docs/email.md`           |
| Non-obvious per-tool design behavior (zsh startup, LSP layering, mrconfig discovery) | `docs/tool-notes.md` |

When using taskfile task tool run it using mise:

```bash
mise exec -- task <task>
```
