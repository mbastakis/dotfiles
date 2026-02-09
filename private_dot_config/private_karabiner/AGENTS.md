# Karabiner-Elements Configuration

Modular build system for complex keyboard modifications with home row mods.

## Structure

| Path                      | Purpose                              |
| ------------------------- | ------------------------------------ |
| `karabiner.json`          | **GENERATED** — do not edit directly |
| `build.sh`                | Build script with HRM config         |
| `src/base.json`           | Base config (devices, parameters)    |
| `src/templates/hrm.json`  | Template for HRM rule generation     |
| `src/rules/*.json`        | Individual rule files (non-HRM)      |
| `README.md`               | Detailed documentation               |

## Commands

| Command       | Purpose                          |
| ------------- | -------------------------------- |
| `./build.sh`  | Rebuild karabiner.json from src/ |

Karabiner-Elements auto-reloads when `karabiner.json` changes.

## Build System

`build.sh` merges `src/base.json` + all `src/rules/*.json` + **generated HRM rules** → `karabiner.json`

Rules sorted alphabetically by filename. Prefix with numbers for order:
```
00-common-words.json
01-bilateral-cancellation.json
02-crossover-timing.json
03-10: HRM rules (generated from HRM_CONFIG)
11-typing-mode-toggle.json
...
16-language-switch.json
```

**Requires**: `jq` (install via `brew install jq`)

### HRM Rules Generation

Home row mod rules (03-10) are **generated dynamically** from:
- `HRM_CONFIG` array in `build.sh` (timing parameters per key)
- `src/templates/hrm.json` (JSON structure with placeholders)

To modify HRM behavior:
- **Timing changes**: Edit `HRM_CONFIG` in `build.sh`
- **Structure changes**: Edit `src/templates/hrm.json`

Config format in `build.sh`:

```bash
# Format: key_code|modifier|finger|hand|streak_ms|held_ms|alone_ms|stack_delay_ms|has_hyper
HRM_CONFIG=(
    "a|left_control|pinky|left|230|270|200|200|0"
    "s|left_option|ring|left|230|250|200|200|0"
    # ... etc
)
```

| Parameter       | Description                                          |
| --------------- | ---------------------------------------------------- |
| `key_code`      | Karabiner key code (a, s, d, f, j, k, l, semicolon)  |
| `modifier`      | Modifier to activate (left_control, left_shift, etc) |
| `finger`        | Finger name (pinky, ring, middle, index)             |
| `hand`          | Hand (left, right)                                   |
| `streak_ms`     | Typing streak window - outputs letter if typed within this window |
| `held_ms`       | Hold threshold for modifier activation               |
| `alone_ms`      | Tap timeout for letter output                        |
| `stack_delay_ms`| Same-hand stacking delayed action timeout            |
| `has_hyper`     | 1 = adds hyper_caps_lock condition, 0 = none         |

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

The config includes 5 layers of protection:
1. **Common word sequences** — `from.simultaneous` rules for rapid cross-hand patterns (e.g., "the")
2. **Bilateral cancellation** — same-hand combos produce letters
3. **Crossover timing** — enforces proper cross-hand timing
4. **Typing streak detection** — disables mods during fast typing
5. **Typing mode toggle** — manual mod disable via Caps+T

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

## Modifying HRM Timing

To adjust timing for a specific finger:
1. Find the key in `HRM_CONFIG` in `build.sh`
2. Modify the timing values (streak_ms, held_ms, alone_ms, stack_delay_ms)
3. Run `./build.sh`

Example - make pinky keys faster:
```bash
# Change from:
"a|left_control|pinky|left|230|270|200|200|0"
# To (faster held threshold):
"a|left_control|pinky|left|230|230|200|200|0"
```

## Gotchas

- **NEVER** edit `karabiner.json` directly — changes overwritten by build
- **HRM rules are generated** — don't create 03-10 JSON files
- **HRM timing**: Edit `HRM_CONFIG` in `build.sh`
- **HRM structure**: Edit `src/templates/hrm.json`
- Each rule file contains a single rule object (not an array)
- Rule files must be valid JSON (use `jq . file.json` to validate)
- Per-finger timing thresholds vary: pinky 270ms → index 150ms
