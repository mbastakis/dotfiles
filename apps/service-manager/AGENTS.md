# Service Manager TUI

OpenTUI React app for managing macOS LaunchAgent services.

## OpenTUI Runtime vs Types

- **TypeScript types are incomplete**: Props like `paddingX`, `paddingY`, `borderTop`, `borderBottom` work at runtime but cause TS errors
- **SelectOption `description` optional at runtime**: Despite type requiring it, `{ name, value }` works fine
- **Run with TS errors**: `bun run src/index.tsx` works even when `tsc --noEmit` fails

## launchctl Modern API

- **Use bootstrap/bootout, not load/unload**: `launchctl bootstrap gui/$(id -u) <plist>` and `launchctl bootout gui/$(id -u)/<label>`
- **GUI domain required**: Must use `gui/<uid>` prefix for user LaunchAgents
- **Exit codes**: `bootout` returns 3 if service wasn't running (not an error)

## Plist Parsing

- **plutil for JSON conversion**: `plutil -convert json -o - <plist>` outputs JSON to stdout
- **`__HOME__` placeholder**: Dotfiles plists use `__HOME__` which must be replaced with actual home dir at install time

## Path Discovery

- **Dotfiles location varies**: Could be `~/dotfiles`, `~/dev/dotfiles`, or `~/.dotfiles`
- **Use `import.meta.dir`**: Bun provides script directory - resolve relative paths from there as fallback
