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

### aws-login build

```bash
# Build manually from source (if needed)
cd ~/.local/share/chezmoi/apps/aws-login && go build -o ~/bin/_aws-login .
```

### Pre-commit hooks

```bash
pre-commit run --all-files  # Run all hooks
pre-commit run shellcheck   # Shellcheck only
pre-commit run gitleaks     # Secrets detection only
```

Hooks: shellcheck (`-x -e SC1091`), gitleaks, yamllint (relaxed), trailing-whitespace,
end-of-file-fixer, check-yaml/toml/json, detect-private-key (excludes `.age`), large files (500KB).
Pre-push: `chezmoi apply --dry-run --force`.

## Apply Order

```
1. Read source + destination state
2. Compute target state (templates, encrypted files)
3. Before scripts (alphabetical):
   00-decrypt-private-key  → key.txt.age → ~/.config/chezmoi/key.txt (passphrase, once)
   01-install-bws          → installs bws CLI (run_once)
   02-install-packages     → brew bundle from Brewfile (run_onchange)
4. File operations (alphabetical by target):
   - Decrypt encrypted_ files (age identity, no prompt)
   - Render .tmpl templates (bitwardenSecrets → chezmoi-bws → bws CLI)
   - Deploy files, directories, symlinks
5. After scripts (alphabetical):
   03-setup                → bat cache, yazi plugins, carapace sync (run_once)
   04-build-aws-login      → builds ~/bin/_aws-login from apps/aws-login (run_onchange)
   macos-settings          → macOS defaults (run_once)
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
    └── ~/.local/share/bws/token → chezmoi-bws → Bitwarden Secrets Manager
                                      └── API keys rendered into ~/.zsh/local.zsh
```

## Key Paths

| Source (chezmoi)             | Target                           | Notes                        |
|------------------------------|----------------------------------|------------------------------|
| `.chezmoi.toml.tmpl`        | `~/.config/chezmoi/chezmoi.toml` | Config, profile, encryption  |
| `key.txt.age`               | _(ignored, source-only)_         | Passphrase-encrypted age key |
| `bin/chezmoi-bws`           | _(ignored, source-only)_         | BWS token wrapper            |
| `apps/aws-login/`           | _(ignored, source-only)_         | Go source for aws-login CLI  |
| `literal_bin/`              | `~/bin/`                         | Shell utility scripts        |
| `private_dot_ssh/`          | `~/.ssh/`                        | SSH keys (encrypted)         |
| `private_dot_config/`       | `~/.config/`                     | App configs                  |
| `.chezmoiscripts/`          | _(lifecycle scripts, not deployed)_ | Before/after scripts      |
| `.chezmoidata.yaml`         | _(template data)_                | Catppuccin Mocha colors      |

## .chezmoiignore

Uses **target-state paths** (not source-state):
- Correct: `.config/foo/bar`
- Wrong: `private_dot_config/foo/bar`

Supports chezmoi template conditionals for OS-specific ignores.

### Operational Gotchas

- `.chezmoiignore` is rendered as a template for many commands (`add`, `status`, `apply`); missing data keys in conditions can break unrelated commands.
- When adding new data keys in `.chezmoi.toml.tmpl`, keep templates compatible with existing keys (for example `.profile`) until `chezmoi init` has been run everywhere.
- For non-interactive checks, prefer `chezmoi apply --dry-run --force`; without `--force`, changed files may trigger TTY prompts and fail in headless shells.
- In this repo, `chezmoi diff` is most reliable with absolute target paths (for example `/Users/mbastakis/.config/git/config`) when diffing a single file.
- `Documents/notes/.obsidian/workspace.json` is volatile UI state (recent files/workspace layout) and should stay ignored to avoid noisy churn and accidental overwrite.
- `glab` rewrites `last_update_check_timestamp` in `.config/glab-cli/config.yml`; expect frequent drift unless that field is ignored or normalized.

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

### Cross-platform

```bash
if [[ "$(uname)" == "Darwin" ]]; then
    # macOS-specific
else
    # Linux-specific
fi
```

## Chezmoi Template Conventions

### OS guards (every .chezmoiscripts/*.tmpl)

```
{{- if ne .chezmoi.os "darwin" }}
exit 0
{{- end }}
```

### Change detection (run_onchange scripts)

```
# hash: {{ include "path/to/file" | sha256sum }}
```

### Template functions used

| Function                          | Purpose                              |
|-----------------------------------|--------------------------------------|
| `{{ .chezmoi.os }}`              | OS detection (`darwin`/`linux`)      |
| `{{ .chezmoi.sourceDir }}`       | Chezmoi source directory path        |
| `{{ .profile }}`                 | `personal` or `dt-work`              |
| `{{ .dtWork }}`                  | Toggle DT work-only config           |
| `{{ .email }}`, `{{ .name }}`    | User data from config                |
| `{{ bitwardenSecrets "uuid" }}`  | Fetch secret from BWS                |
| `{{ include "file" \| sha256sum }}` | File content hash for change detection |
| `{{ env "VAR" }}`               | Read environment variable            |
| `{{ promptChoiceOnce ... }}`     | Interactive prompt (cached)          |
| `{{ value \| quote }}`          | Quote for TOML output                |
| `{{ value \| trim }}`           | Trim whitespace from secrets         |

### Whitespace control

Always use `{{-` and `-}}` to trim surrounding whitespace in template tags.

## Neovim Config (private_dot_config/nvim/)

- **2-space indent**, double quotes, trailing commas
- Plugin specs: `return { "author/plugin", opts = { ... } }` (lazy.nvim)
- Keymaps: `vim.keymap.set("n", "<leader>key", func, { desc = "Category: Action" })`
- LSP configs: `after/lsp/<server>.lua` with `vim.lsp.config()`
- Formatter: stylua. Linter: selene (permissive, `std = "lua51"`)

## Zsh Config (dot_zsh/)

Load order: exports → plugins → completions → tools → aliases → functions →
fzf → fzf-tab → keybindings → direnv → local

- Conditional sourcing: `[[ -f "$file" ]] && source "$file"`
- Tool init: `command -v tool &>/dev/null && eval "$(tool init zsh)"`
- Startup caching: `[[ ! -f "$cache" ]] || [[ "$bin" -nt "$cache" ]]`
- ZLE widgets: define function → `zle -N name` → `bindkey '^X' name`

## Karabiner (private_dot_config/private_karabiner/)

Build system only — `karabiner.json` is generated, never edit directly.
Only `karabiner.json` is deployed to target; `build.sh` and `src/` stay in source.

```bash
# Rebuild from chezmoi source dir:
cd ~/.local/share/chezmoi/private_dot_config/private_karabiner && ./build.sh
```
