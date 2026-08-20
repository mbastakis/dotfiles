# Zsh Configuration

Modular zsh config lives at `~/.config/zsh/`, sourced by `~/.config/zsh/.zshrc`.
`ZDOTDIR` is set in `~/.zshenv` to point here.

## Files

| File                            | Purpose                              |
| ------------------------------- | ------------------------------------ |
| `exports.zsh`                   | Interactive variables and secrets    |
| `plugins.zsh`                   | Zinit plugin manager, compinit       |
| `completions.zsh`               | Tool-provided and cached completions   |
| `tools.zsh`                     | atuin, zoxide, starship              |
| `aliases.zsh`                   | Command shortcuts                    |
| `functions.zsh`                 | Custom shell functions               |
| `fzf.zsh`                       | FZF configuration                    |
| `fzf-tab.zsh`                   | FZF completion menu                  |
| `keybindings.zsh`               | Custom ZLE widgets and bindings      |
| `direnv.zsh`                    | Direnv hook                          |
| `shift-select-enhancements.zsh` | Clipboard integration for selections |

## Load Order (Critical)

Files sourced in this order (defined in `.zshrc`):

```
exports → plugins → completions → tools → aliases → functions → fzf → fzf-tab → keybindings
```

Dependencies:

- `plugins.zsh` runs `compinit` — must load before `completions.zsh`
- `fzf-tab.zsh` configures plugin loaded in `plugins.zsh`
- `keybindings.zsh` uses `ftext-widget` from `functions.zsh`

## Commands

| Command                 | Purpose             |
| ----------------------- | ------------------- |
| `source $ZDOTDIR/.zshrc` | Reload config      |
| `reload`                | Fresh shell         |
| `zinit update`          | Update all plugins  |
| `zinit self-update`     | Update zinit itself |

## Code Style

```zsh
#!/usr/bin/env zsh

# Conditional sourcing
[[ -f "$file" ]] && source "$file"

# Tool existence check
command -v tool &>/dev/null && eval "$(tool init zsh)"

# ZLE widget pattern
function widget_name() {
  # widget logic
  zle reset-prompt
}
zle -N widget_name
bindkey '^X' widget_name
```

## Adding New Config

| Type              | Location          | Notes                          |
| ----------------- | ----------------- | ------------------------------ |
| Aliases           | `aliases.zsh`     | Simple command shortcuts       |
| Functions         | `functions.zsh`   | Complex multi-line logic       |
| Tool integrations | `tools.zsh`       | `eval "$(tool init zsh)"`      |
| Completions       | `completions.zsh` | Tool-provided or cache-generated definitions |
| Keybindings       | `keybindings.zsh` | ZLE widgets + bindkey          |
| Environment       | `exports.zsh`     | API keys, interactive variables, profile PATH |

## Zsh Shell Types and File Loading

Background processes (launchd, cron, opencode subprocesses) spawn non-interactive shells:

| Shell invocation | Files loaded            | Example use case            |
| ---------------- | ----------------------- | --------------------------- |
| `zsh -c 'cmd'`   | `.zshenv` only          | opencode bash tool, scripts |
| `zsh -l`         | `.zshenv` + `.zprofile` | login shells                |
| `zsh -i`         | `.zshenv` + `.zshrc`    | interactive terminals       |

**Critical**: Put PATH additions needed by background processes in `dot_zshenv.tmpl` (`.zshenv`), not `.zshrc`. `.zshenv` stays at `$HOME`; everything else is loaded from `$ZDOTDIR` (`~/.config/zsh/`).

## Gotchas

- All zsh config lives in `~/.config/zsh/` via `ZDOTDIR`. The chezmoi source is `private_dot_config/zsh/`.
- **Background process PATH**: Homebrew (`/opt/homebrew/bin`) must be in `dot_zshenv.tmpl` for launchd services to find brew-installed binaries
- `shift-select-enhancements.zsh` loaded via zinit atload hook, not directly sourced
- `exports.zsh` is generated from `private_dot_config/zsh/exports.zsh.tmpl`; it contains both interactive exports and BWS-rendered secrets

## Startup Performance

Cache slow tool init output to `~/.cache/` for faster shell startup:

```zsh
# Pattern: cache if missing OR binary newer than cache
_cache="$HOME/.cache/tool-init.zsh"
_bin="$(command -v tool)"
if [[ ! -f "$_cache" ]] || [[ "$_bin" -nt "$_cache" ]]; then
  tool init zsh > "$_cache"
fi
source "$_cache"
```

Generated completion scripts are centralized in `completions.zsh` and stored under `$ZSH_COMPLETION_CACHE_DIR`; package-managed native definitions come from each tool's installation. The `-nt` (newer than) operator invalidates cache when a binary updates.
