# OpenCode Configuration

Config for OpenCode v2 (`opencode2`), written in **native v2 syntax** since
2026-08-20. The v1 `opencode` binary stays brew-installed but can no longer
read this config (git history holds the last v1-syntax version).

## Structure

| Path | Purpose |
|---|---|
| `opencode.jsonc` | Shared engine config (native v2): providers, permissions rules, MCP, agents, references |
| `cli.json` | Terminal-client config (chezmoi-managed): theme, sidebar/tabs, attention, full explicit keybind map |
| `service.json` | v2 service config: port 4097, basic-auth password, provider env (runtime-owned, NOT chezmoi-managed) |
| `commands/*.md` | Custom slash commands (v2 plural layout) |
| `agents/*.md` | Agents with native v2 frontmatter (`permissions` rule arrays, `request.body` overlays) |
| `skills/*/SKILL.md` | OpenCode-only skills |
| `tui-plugins/wcs-usage.js` | v2 client plugin: WCS quota display, loaded via `cli.json` `plugins` |
| `~/.agents/skills/*/SKILL.md` | Shared harness-agnostic skills managed from `private_dot_agents/skills/` |

## Commands

| Command | Purpose |
|---|---|
| `oc` / `occ` | New session / continue — thin wrappers around `opencode2` |
| `opencode2 service status\|start\|stop\|restart` | Background service lifecycle |
| `opencode2 pair` | Service URL, password, and pairing QR |
| `ocserve` (`opencode-server`) | Service + oauth2-proxy + Tailscale Serve stack |
| `opencode` | v1 escape hatch (binary only; cannot read this config anymore) |

## Providers

The default model is `wcs/gpt` through the private WhoCaresSoftware gateway at
`https://ai.whocaressoftware.com/v1`. Providers use the native v2 form:
`package: "aisdk:@ai-sdk/openai-compatible"` + `settings.baseURL` +
`settings.apiKey: "{env:VAR}"`. Models use `modelID`/`capabilities`/`limit`,
variants are arrays of `{id, settings}`, and interleaved reasoning is
`compatibility.reasoningField`. `experimental.policies` (provider.use rules)
replaces the old `enabled_providers` list.

Provider credentials reach the background service via
`opencode2 service set env` (pushed by chezmoi step 10 from the rendered
`exports.zsh`), not from the shell environment. The `{env:VAR}` placeholders
in `opencode.jsonc` resolve against that service environment — never put
literal keys in the config.

## Remote Stack (designated Mac)

- opencode2 background service on loopback port `4097` (basic auth; serves
  the HTTP API and the built-in web UI)
- oauth2-proxy (Authentik OIDC) on loopback port `4180`
- Tailscale Serve routes `https://code.mbastakis.com` → proxy → service

The launchd unit `com.mbastakis.opencode-server` only runs the idempotent
`opencode2 service start` at login and every 5 minutes; the service manages
its own process and hot-reloads config, agents, commands, and skills. Restarts
are needed only for binary updates: `opencode2 service restart`. Clients
rediscover the service and resume their sessions from the shared SQLite DB.

## Permissions

Native v2 ordered rule array (`{action, resource, effect}`), **last matching
rule wins**: broad `shell */edit/external_directory` allow first, then asks
for destructive filesystem, git-history, cluster, and infrastructure
operations. v2's `*` crosses spaces, so single patterns like
`kubectl* apply*` replace the old `X*` + `X * Y*` pairs, and a pattern ending
in `" *"` also matches the bare command. Per-agent rules in the agent
frontmatter are appended after these (so they override).

## cli.json

Chezmoi-managed since 2026-08-20. Notable choices: catppuccin theme,
sidebar `auto`, tabs `vertical` + `global` scope, attention fully enabled
(notifications + sounds, volume 0.4), mouse capture, compact paste, split
diff view with file tree, and a **full explicit keybind map** (all 217
actions of beta-17728, defaults pinned) with leader `ctrl+x` and custom
bindings: `<leader>f` fork, `<leader>p` permission auto-approve toggle,
`<leader>z`/`<leader>j`/`<leader>k` prompt stash/pop/list, `<leader>v`
variant list. The TUI settings UI (Ctrl+P → Open settings) writes this file
live — port deliberate changes back to the chezmoi source or they revert on
apply.

## Validation

```bash
opencode-server status
opencode2 debug config   # config sources; confirms native v2 parse
opencode2 debug agents   # resolved agents incl. merged permission rules
mise exec -- task check
```

## Gotchas

- Agent markdown files require exact YAML frontmatter delimiters.
- Model IDs must match provider format exactly; unknown `#variant` suffixes
  are hard resolution errors in v2.
- `service.json` is runtime-owned; keep it out of chezmoi.
- The terminal client rewrites `cli.json` in place and silently drops keybind
  IDs the running build doesn't know — after a binary update, diff live vs
  source before applying.
- Keybind action IDs are validated: an unknown ID is rejected, so prune the
  explicit map when a beta build removes an action.
