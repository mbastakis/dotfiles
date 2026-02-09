# Karabiner-Elements Configuration

Advanced keyboard customization using Home Row Mods (HRM) with multiple anti-misfire protection layers.

## Features

- **Home Row Mods (GASC Layout)**: Use home row keys as modifiers when held
- **Hyper Key**: Caps Lock becomes a navigation layer key (tap for Escape)
- **Anti-Misfire Protection**: Multiple layers prevent accidental modifier activation during fast typing
- **Typing Mode**: Toggle to disable all HRM behavior temporarily
- **Modular Build System**: Individual rule files compiled into final config

## Quick Start

```bash
# Build the configuration
cd dot-config/karabiner
./build.sh

# The generated karabiner.json is automatically loaded by Karabiner-Elements
```

**Requirements:** `jq` (install with `brew install jq`)

## Directory Structure

```
dot-config/karabiner/
├── karabiner.json          # Generated output (DO NOT EDIT DIRECTLY)
├── build.sh                # Build script that merges rules
├── README.md               # This file
└── src/
    ├── base.json           # Base config (profile, devices, parameters)
    └── rules/              # Individual rule files (processed alphabetically)
        ├── 01-bilateral-cancellation.json
        ├── 02-crossover-timing.json
        ├── 03-hrm-left-a.json
        ├── ...
        └── 15-hyper-navigation.json
```

## Home Row Mods Layout

```
Left Hand                          Right Hand
┌─────┬─────┬─────┬─────┐         ┌─────┬─────┬─────┬─────┐
│  A  │  S  │  D  │  F  │         │  J  │  K  │  L  │  ;  │
│ Ctrl│ Opt │ Cmd │Shift│         │Shift│ Cmd │ Opt │ Ctrl│
└─────┴─────┴─────┴─────┘         └─────┴─────┴─────┴─────┘
Pinky  Ring Middle Index          Index Middle Ring  Pinky
```

**Behavior:**
- **Tap**: Output the letter
- **Hold**: Activate the modifier
- **Roll with same-hand key**: Output both letters (bilateral cancellation)

## Hyper Key Navigation

Hold **Caps Lock** to access navigation layer:

| Key | Action |
|-----|--------|
| H | Escape |
| J | Left Arrow |
| K | Down Arrow |
| I | Up Arrow |
| L | Right Arrow |
| D | Start of Line (Cmd+Left) |
| F | End of Line (Cmd+Right) |
| U | Page Up |
| N | Page Down |
| , | Page Down |
| . | Page Up |
| Y | Home |
| O | End |
| M | Backspace |
| ; | Option (modifier) |

**Caps Lock alone** = Escape

## Anti-Misfire Protection

Four layers prevent accidental modifier activation:

### 1. Bilateral Cancellation
When you roll keys on the same hand (e.g., hold `a`, tap `s`), both letters are output instead of triggering Ctrl+S.

### 2. Crossover Timing (80ms)
If you press a cross-hand key within 80ms of pressing an HRM key, the modifier is cancelled. This catches fast typing like "ask" where you might hit `a`, then quickly `s`, then `k`.

### 3. Typing Streak Detection (230ms)
If you've typed any key within the last 230ms, HRM keys output their letter immediately instead of waiting to see if you'll hold them.

### 4. Typing Mode Toggle
Press **Right Cmd + Space** (or hold `k` + Space) to disable all HRM behavior. A notification appears: "TYPING MODE ON". Toggle off with the same shortcut or **Left Cmd + Space**.

## Other Features

### Double-Tap Right Shift for Caps Lock
Quickly tap Right Shift twice within 300ms to toggle Caps Lock.

## Rule Files Reference

| File | Description |
|------|-------------|
| `01-bilateral-cancellation.json` | Same-hand rollover outputs both letters |
| `02-crossover-timing.json` | 80ms cross-hand shortcut cancellation |
| `03-hrm-left-a.json` | A key: tap=a, hold=Control |
| `04-hrm-left-s.json` | S key: tap=s, hold=Option |
| `05-hrm-left-d.json` | D key: tap=d, hold=Command |
| `06-hrm-left-f.json` | F key: tap=f, hold=Shift |
| `07-hrm-right-j.json` | J key: tap=j, hold=Shift |
| `08-hrm-right-k.json` | K key: tap=k, hold=Command |
| `09-hrm-right-l.json` | L key: tap=l, hold=Option |
| `10-hrm-right-semicolon.json` | ; key: tap=;, hold=Control |
| `11-typing-mode-toggle.json` | Right Cmd+Space toggles typing mode |
| `12-typing-activity-tracking.json` | Tracks keypresses for streak detection |
| `13-hyper-key.json` | Caps Lock to hyper mode (tap=Escape) |
| `14-double-tap-caps.json` | Double-tap right shift for Caps Lock |
| `15-hyper-navigation.json` | Hyper+keys for arrows and navigation |

## Timing Parameters

Different fingers have different hold thresholds (in milliseconds):

| Finger | Keys | Hold Threshold | Typing Streak |
|--------|------|----------------|---------------|
| Pinky | A, ; | 270ms | 230ms |
| Ring | S, L | 250ms | 230ms |
| Middle | D, K | 230ms | 230ms |
| Index | F, J | 150ms | 70ms |

Index fingers use faster timing since Shift is used more frequently.

## Adding New Rules

### Create a New Rule File

1. Create a file in `src/rules/` with a numbered prefix:
   ```bash
   touch src/rules/16-my-new-rule.json
   ```

2. Add the rule structure:
   ```json
   {
       "description": "My new rule description",
       "manipulators": [
           {
               "type": "basic",
               "from": {
                   "key_code": "f1",
                   "modifiers": { "optional": ["any"] }
               },
               "to": [
                   { "key_code": "mission_control" }
               ]
           }
       ]
   }
   ```

3. Rebuild:
   ```bash
   ./build.sh
   ```

### Rule Ordering

Files are processed alphabetically by filename. Use numbered prefixes to control evaluation order. **First matching rule wins**, so order matters for rules that might conflict.

### Common Patterns

**Simple key remap:**
```json
{
    "type": "basic",
    "from": { "key_code": "caps_lock" },
    "to": [{ "key_code": "escape" }]
}
```

**Conditional on variable:**
```json
{
    "type": "basic",
    "conditions": [
        { "type": "variable_if", "name": "my_mode", "value": 1 }
    ],
    "from": { "key_code": "j" },
    "to": [{ "key_code": "left_arrow" }]
}
```

**Tap vs Hold:**
```json
{
    "type": "basic",
    "from": { "key_code": "spacebar" },
    "to": [{ "key_code": "left_shift" }],
    "to_if_alone": [{ "key_code": "spacebar" }],
    "parameters": {
        "basic.to_if_alone_timeout_milliseconds": 200
    }
}
```

**Set a variable:**
```json
{
    "to": [
        {
            "set_variable": {
                "name": "my_layer",
                "value": 1,
                "key_up_value": 0
            }
        }
    ]
}
```

## State Variables

| Variable | Purpose |
|----------|---------|
| `left_hrm` / `right_hrm` | HRM key is pressed |
| `left_mod_active` / `right_mod_active` | Modifier is activated (held long enough) |
| `left_{finger}_held` | Specific finger tracking (pinky/ring/middle/index) |
| `left_hand_press_time` / `right_hand_press_time` | Timestamp for crossover timing |
| `last_keypress_time` | Timestamp for typing streak detection |
| `typing_mode` | Typing mode enabled (1) or disabled (0) |
| `hyper_caps_lock` | Hyper key is held |

## Troubleshooting

### View Logs
```bash
tail -f ~/.local/share/karabiner/log/console_user_server.log
```

Or open Karabiner-Elements Settings > Log tab.

### Test Key Events
Use **Karabiner-EventViewer** (included with Karabiner-Elements) to see what key codes and events are being generated.

### Validate JSON
The build script validates JSON automatically. For manual checks:
```bash
jq empty karabiner.json
```

### Reset to Defaults
If something goes wrong, you can disable complex modifications in Karabiner-Elements Settings, or delete rules from the Complex Modifications tab.

## Resources

- [Karabiner-Elements Documentation](https://karabiner-elements.pqrs.org/docs/)
- [Complex Modifications Reference](https://karabiner-elements.pqrs.org/docs/json/)
- [Community Rules](https://ke-complex-modifications.pqrs.org/)
