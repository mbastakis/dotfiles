# Nix Manager TUI

OpenTUI-based TUI for managing Homebrew packages vs Nix flake configuration.

## OpenTUI API Notes

- **TypeScript types incomplete**: `paddingX`, `paddingY`, `borderTop`, `borderBottom` work at runtime but cause TS errors - ignore them
- **SelectOption description optional**: Despite types, `{ name, value }` works at runtime
- **Border styles**: Use `borderStyle="rounded"` for Catppuccin aesthetic consistency
- **List overflow prevention**: Must use `overflow="hidden"` AND explicit `height` on containers. Each row needs `height={1}`. Calculate chrome height accurately (header + status bar padding/borders).

## Flake.nix Parsing

- **masApps uses attribute set syntax**: `homebrew.masApps = { "Name" = id; };` not array like brews/casks
- **Compare masApps by ID, not name**: Names can differ between `mas list` output and flake.nix
- **mas CLI output format**: `mas list` outputs `123456789 App Name (1.2.3)` - parse with `/^(\d+)\s+(.+?)\s+\(/`

## CLI Mode

Supports non-interactive usage:
- `nix-manager --list` - All packages with status
- `nix-manager --diff` - Only differences (extra/missing)
- `nix-manager --help` - Usage info

## File Dependencies

- `lib/flake.ts` hardcodes path to `~/dev/dotfiles/dot-config/nix-darwin/flake.nix`
- Wrapper script at `dot-bin/nix-manager` runs directly from `apps/nix-manager/`
