# Service Manager TUI

OpenTUI React app for managing macOS services.

## Architecture

Service configs live in `~/.config/service-manager/*.toml` (stowed from `dot-config/service-manager/`).
The TUI reads these configs, generates plist files, and manages service installation/lifecycle.

### TOML Config Format

```toml
enabled = true

[service]
label = "ai.opencode.serve"
program = ["/opt/homebrew/bin/opencode", "serve"]
run_at_load = true
keep_alive = true
working_directory = "~"

[service.environment]
AWS_PROFILE = "claude-code"

[logs]
stdout = "~/.local/share/opencode/serve.log"
stderr = "~/.local/share/opencode/serve.error.log"
```

### CLI Commands

- `svc` - Launch interactive TUI
- `svc sync` - Sync all services from config files (install enabled, uninstall disabled)
- `svc --help` - Show help

## OpenTUI Runtime vs Types

- **TypeScript types are incomplete**: Props like `paddingX`, `paddingY`, `borderTop`, `borderBottom` work at runtime but cause TS errors
- **SelectOption `description` optional at runtime**: Despite type requiring it, `{ name, value }` works fine
- **Run with TS errors**: `bun run src/index.tsx` works even when `tsc --noEmit` fails
- **useState setter types**: When exposing `setScrollOffset` from hooks, use `React.Dispatch<React.SetStateAction<number>>` not `(value: number) => void` to allow updater functions like `(prev) => prev + 1`
- **Keyboard case sensitivity**: `key.name` is always lowercase for letters - use `key.shift` to detect uppercase (e.g., `case "r": if (key.shift) { /* R */ } else { /* r */ }`)

## Status Polling

- **Track previous state**: Store last known status in a ref, compare on each poll, only call refresh callback when status actually changes - avoids unnecessary re-renders
- **Test with launchctl**: `launchctl bootout gui/$(id -u)/<label>` to manually stop service and verify TUI auto-updates

## launchctl Modern API

- **Use bootstrap/bootout, not load/unload**: `launchctl bootstrap gui/$(id -u) <plist>` and `launchctl bootout gui/$(id -u)/<label>`
- **GUI domain required**: Must use `gui/<uid>` prefix for user services
- **Exit codes**: `bootout` returns 3 if service wasn't running (not an error)
- **Reinstall requires full uninstall first**: `startService`'s "best effort" bootout swallows failures - when updating plist configs, must call `uninstallService` (stop + remove plist) before `installService` to ensure old config isn't still running
- **One-shot service success**: `status === "stopped" && exitCode === 0` means successful completion - use "ran" not "started" in user messaging
- **Definitive failure detection**: `status === "stopped" && exitCode !== 0` means service crashed - exit retry loops early instead of waiting full timeout

## Plist Generation

- Plists are generated from TOML configs at install time
- Path expansion: `~` is expanded to home directory **only at string start** (e.g., `~/.config` expands, but `/foo:~/.bar` does not)
- Environment variables include HOME and PATH by default
- **PATH gotcha**: Use absolute paths in `[service.environment].PATH`, not `~` — the `expandPath()` function only handles `~` at position 0

## TUI Navigation

- **Guard empty arrays**: Navigation handlers (`j/k/g/G`) must check `services.length === 0` before updating index - `Math.min(length - 1, i + 1)` returns -1 when length is 0
- **Applies to all scrollable lists**: Same pattern needed for log viewer scroll offset with `logLines.length`
- **Floor scroll calculations**: `Math.max(0, logLines.length - 10)` to prevent negative offset when list is shorter than viewport

## Design Decisions

- **No separate install action**: Enable/disable toggle (`e`) handles install+start and stop+uninstall - separate install key is redundant and confusing
