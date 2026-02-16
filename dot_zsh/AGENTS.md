# Zsh Configuration

Modular zsh config files symlinked to `~/.zsh/`, sourced by `~/.zshrc`.

## Files

| File                            | Purpose                              |
| ------------------------------- | ------------------------------------ |
| `exports.zsh`                   | Environment variables (PAGER, LESS)  |
| `plugins.zsh`                   | Zinit plugin manager, compinit       |
| `completions.zsh`               | Tool-specific completions            |
| `tools.zsh`                     | atuin, zoxide, starship              |
| `aliases.zsh`                   | Command shortcuts                    |
| `functions.zsh`                 | Custom shell functions               |
| `fzf.zsh`                       | FZF configuration                    |
| `fzf-tab.zsh`                   | FZF completion menu                  |
| `keybindings.zsh`               | Ctrl-F, Ctrl-G, Alt-C bindings       |
| `direnv.zsh`                    | Direnv hook                          |
| `shift-select-enhancements.zsh` | Clipboard integration for selections |
| `local.zsh`                     | Machine-specific (gitignored)        |

## Load Order (Critical)

Files sourced in this order (defined in `dot-zshrc`):

```
exports → plugins → completions → tools → aliases → functions → fzf → fzf-tab → keybindings → direnv → local
```

Dependencies:

- `plugins.zsh` runs `compinit` — must load before `completions.zsh`
- `fzf-tab.zsh` configures plugin loaded in `plugins.zsh`
- `keybindings.zsh` uses `ftext-widget` from `functions.zsh`

## Commands

| Command             | Purpose             |
| ------------------- | ------------------- |
| `source ~/.zshrc`   | Reload config       |
| `reload`            | Alias for above     |
| `zinit update`      | Update all plugins  |
| `zinit self-update` | Update zinit itself |

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
| Keybindings       | `keybindings.zsh` | ZLE widgets + bindkey          |
| Machine-specific  | `local.zsh`       | API keys, local PATH overrides |

## Zsh Shell Types and File Loading

Background processes (launchd, cron, opencode subprocesses) spawn non-interactive shells:

| Shell invocation | Files loaded | Example use case |
|------------------|--------------|------------------|
| `zsh -c 'cmd'` | `.zshenv` only | opencode bash tool, scripts |
| `zsh -l` | `.zshenv` + `.zprofile` | login shells |
| `zsh -i` | `.zshenv` + `.zshrc` | interactive terminals |

**Critical**: Put PATH additions needed by background processes in `dot-zshenv`, not `dot-zshrc`. The `exports.zsh` file is only sourced by interactive shells.

## Gotchas

- **Do not** add zsh files to `dot-config/` — all zsh config goes in `dot-zsh/`
- **Background process PATH**: Homebrew (`/opt/homebrew/bin`) must be in `dot-zshenv` for launchd services to find brew-installed binaries
- `shift-select-enhancements.zsh` loaded via zinit atload hook, not directly sourced
- `local.zsh` is gitignored — copy from `local.zsh.example` as template
- `obsidian-cli.zsh` is NOT in default load order — source from `local.zsh` if needed

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

Used for: `brew shellenv`, `carapace _carapace zsh`. The `-nt` (newer than) operator invalidates cache when binary updates.
