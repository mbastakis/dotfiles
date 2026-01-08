# Karabiner-Elements Configuration

Modular build system for complex keyboard modifications with home row mods.

## Structure

| Path                 | Purpose                              |
| -------------------- | ------------------------------------ |
| `karabiner.json`     | **GENERATED** — do not edit directly |
| `build.sh`           | Merges src/ into karabiner.json      |
| `src/base.json`      | Base config (devices, parameters)    |
| `src/rules/*.json`   | Individual rule files                |
| `README.md`          | Detailed documentation               |

## Commands

| Command       | Purpose                          |
| ------------- | -------------------------------- |
| `./build.sh`  | Rebuild karabiner.json from src/ |

Karabiner-Elements auto-reloads when `karabiner.json` changes.

## Build System

`build.sh` merges `src/base.json` + all `src/rules/*.json` → `karabiner.json`

Rules sorted alphabetically by filename. Prefix with numbers for order:
```
01-bilateral-cancellation.json
02-crossover-timing.json
03-hrm-left-a.json
...
15-hyper-navigation.json
16-language-switch.json
```

**Requires**: `jq` (install via `brew install jq`)

### Device Filtering

By default, all rules apply only to the **built-in keyboard**. This prevents home row mods from interfering with external keyboards.

To make a rule work on **all devices**, add its filename to `ALL_DEVICES_RULES` in `build.sh`:

```bash
ALL_DEVICES_RULES=(
    "16-language-switch.json"
)
```

Rules in this array skip the `device_if` condition and work on any keyboard.

## Home Row Mods Layout (GASC)

| Key | Modifier | Key | Modifier |
| --- | -------- | --- | -------- |
| A   | Ctrl     | ;   | Ctrl     |
| S   | Option   | L   | Option   |
| D   | Command  | K   | Command  |
| F   | Shift    | J   | Shift    |

## Anti-Misfire Protection

The config includes 4 layers of protection:
1. **Bilateral cancellation** — same-hand combos produce letters
2. **Crossover timing** — enforces proper cross-hand timing
3. **Typing streak detection** — disables mods during fast typing
4. **Typing mode toggle** — manual mod disable via Caps+T

## Adding Rules

1. Create `src/rules/<NN>-<name>.json` with single rule object:
```json
{
  "description": "Rule description",
  "manipulators": [...]
}
```
2. Run `./build.sh`
3. Karabiner auto-reloads

## Gotchas

- **NEVER** edit `karabiner.json` directly — changes overwritten by build
- Each rule file contains a single rule object (not an array)
- Rule files must be valid JSON (use `jq . file.json` to validate)
- Per-finger timing thresholds vary: pinky 270ms → index 150ms
