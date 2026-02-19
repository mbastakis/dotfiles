# mbastakis dotfiles (chezmoi)

## Install

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply mbastakis
```

This single command installs chezmoi, clones the repo, installs all
prerequisites (Homebrew, age, bws) via chezmoi `before` scripts, decrypts
encrypted files, and applies everything. You will be prompted for:

1. **DT work config** — `yes` or `no` (personal baseline is always enabled)
2. **Age passphrase** — the single unlock secret for all encrypted files

## Daily use

```bash
chezmoi update
chezmoi diff
chezmoi apply
```
