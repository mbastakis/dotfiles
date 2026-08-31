# Dotfiles (chezmoi)

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
## Encryption

Single age keypair, passphrase-protected. Passphrase only needed on first `chezmoi init`.

```
key.txt.age (in repo, passphrase-encrypted)
    ↓ decrypted once by run_onchange_before_00
~/.config/chezmoi/key.txt (plaintext identity)
    ↓ used by chezmoi builtin age (no further prompts)
    ├── ~/.ssh/id_ed25519
    ├── ~/.supermaven/config.json
    └── ~/.local/share/bws/token → ~/.zshenv exports BWS_ACCESS_TOKEN globally
                                      └── bws renders API keys into ~/.config/zsh/exports.zsh
```

## .chezmoiignore

Uses **target-state paths** (not source-state):

- Correct: `.config/foo/bar`
- Wrong: `private_dot_config/foo/bar`

### Operational Gotchas

- `.chezmoiignore` is rendered as a template for many commands (`add`, `status`, `apply`); missing data keys in conditions can break unrelated commands.
- When removing data keys from `.chezmoi.toml.tmpl`, remove all template and ignore consumers in the same change; existing rendered configs may retain unused keys until `chezmoi init` regenerates them.
- For non-interactive checks, prefer `chezmoi apply --dry-run --force`; without `--force`, changed files may trigger TTY prompts and fail in headless shells.
- In this repo, `chezmoi diff` is most reliable with absolute target paths (for example `/Users/mbastakis/.config/git/config`) when diffing a single file.
- Any new repo-only directory (like `docs/`) must be added to `.chezmoiignore` or chezmoi will deploy it to `~/`. The ignore file uses target-state paths, so `docs/` not `literal_docs/`.

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


## Zsh Config (private_dot_config/zsh/)

`dot_zshenv.tmpl` still renders to `~/.zshenv`; interactive/login zsh config lives in `private_dot_config/zsh/` and is loaded via `ZDOTDIR=~/.config/zsh`.
