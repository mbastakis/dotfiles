#!/usr/bin/env bash
# Build karabiner.json from modular source files
# Usage: ./build.sh
#
# Merges base.json + rules/*.json + generated HRM rules -> karabiner.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
OUTPUT_FILE="$SCRIPT_DIR/karabiner.json"
HRM_TEMPLATE="$SRC_DIR/templates/hrm.json"

# Rules that work on ALL devices (not just built-in keyboard)
ALL_DEVICES_RULES=("16-language-switch.json")

# ============================================================================
# HRM Configuration: key|modifier|finger|hand|streak|held|alone|stack|hyper
# ============================================================================
HRM_CONFIG=(
    # Left hand: a=ctrl, s=opt, d=cmd, f=shift
    "a|left_control|pinky|left|160|200|200|120|0"
    "s|left_option|ring|left|160|200|200|120|0"
    "d|left_command|middle|left|160|200|200|120|1"
    "f|left_shift|index|left|50|130|150|120|1"
    # Right hand: j=shift, k=cmd, l=opt, ;=ctrl
    "j|right_shift|index|right|50|130|150|120|1"
    "k|right_command|middle|right|160|200|200|120|1"
    "l|right_option|ring|right|160|200|200|120|1"
    "semicolon|right_control|pinky|right|160|200|200|120|1"
)

# Device condition for built-in keyboard
DEVICE_CONDITION='{"type": "device_if", "identifiers": [{"is_built_in_keyboard": true}]}'

# ============================================================================
# Validation
# ============================================================================
command -v jq &>/dev/null || { echo "Error: jq required (brew install jq)"; exit 1; }
[[ -f "$SRC_DIR/base.json" ]] || { echo "Error: $SRC_DIR/base.json not found"; exit 1; }
[[ -f "$HRM_TEMPLATE" ]] || { echo "Error: $HRM_TEMPLATE not found"; exit 1; }
[[ -d "$SRC_DIR/rules" ]] || { echo "Error: $SRC_DIR/rules not found"; exit 1; }

echo "Building karabiner.json..."

# ============================================================================
# Helper functions
# ============================================================================
is_all_devices_rule() {
    local filename="$1"
    for rule in "${ALL_DEVICES_RULES[@]}"; do
        [[ "$filename" == "$rule" ]] && return 0
    done
    return 1
}

add_device_condition() {
    jq --argjson device "$DEVICE_CONDITION" '
        .manipulators = [.manipulators[] | 
            .conditions = (.conditions // []) + [$device]
        ]
    '
}

# ============================================================================
# Generate single HRM rule from template
# ============================================================================
generate_hrm_rule() {
    local key_code="$1" modifier="$2" finger="$3" hand="$4"
    local streak_ms="$5" held_ms="$6" alone_ms="$7" stack_delay_ms="$8" has_hyper="$9"

    # Derive variable names
    local hand_hrm="${hand}_hrm"
    local hand_mod_active="${hand}_mod_active"
    local hand_press_time="${hand}_hand_press_time"
    local finger_held="${hand}_${finger}_held"
    local opposite_hrm opposite_mod_active
    
    if [[ "$hand" == "left" ]]; then
        opposite_hrm="right_hrm"; opposite_mod_active="left_mod_active"
    else
        opposite_hrm="left_hrm"; opposite_mod_active="right_mod_active"
    fi

    # Modifier display names
    local mod_short mod_full
    case "$modifier" in
        *control*) mod_short="ctrl"; mod_full="control" ;;
        *option*)  mod_short="opt";  mod_full="option" ;;
        *command*) mod_short="cmd";  mod_full="command" ;;
        *shift*)   mod_short="shift"; mod_full="shift" ;;
    esac

    # Key display (semicolon -> ; for manipulator descriptions)
    local key_display="$key_code"
    [[ "$key_code" == "semicolon" ]] && key_display=";"

    # Finger description
    local finger_name
    case "$finger" in
        pinky)  finger_name="pinky finger" ;;
        ring)   finger_name="ring finger" ;;
        middle) finger_name="middle finger" ;;
        index)  finger_name="index finger (fast, shorter streak)" ;;
    esac

    # Conditional parts
    local lazy_suffix=""
    [[ "$modifier" != *"shift"* ]] && lazy_suffix=', "lazy": true'
    
    local streak_suffix=""
    [[ "$finger" == "index" ]] && streak_suffix=" (shorter window for shift)"
    
    local hyper_condition=""
    [[ "$has_hyper" == "1" ]] && hyper_condition='{ "type": "variable_if", "name": "hyper_caps_lock", "value": 0 },'

    # Substitute placeholders in template
    sed -e "s/{{KEY_CODE}}/$key_code/g" \
        -e "s/{{KEY_DISPLAY}}/$key_display/g" \
        -e "s/{{MODIFIER}}/$modifier/g" \
        -e "s/{{MOD_SHORT}}/$mod_short/g" \
        -e "s/{{MOD_FULL}}/$mod_full/g" \
        -e "s/{{FINGER}}/$finger/g" \
        -e "s/{{FINGER_NAME}}/$finger_name/g" \
        -e "s/{{FINGER_HELD}}/$finger_held/g" \
        -e "s/{{HAND}}/$hand/g" \
        -e "s/{{HAND_HRM}}/$hand_hrm/g" \
        -e "s/{{HAND_MOD_ACTIVE}}/$hand_mod_active/g" \
        -e "s/{{HAND_PRESS_TIME}}/$hand_press_time/g" \
        -e "s/{{OPPOSITE_HRM}}/$opposite_hrm/g" \
        -e "s/{{OPPOSITE_MOD_ACTIVE}}/$opposite_mod_active/g" \
        -e "s/{{STREAK_MS}}/$streak_ms/g" \
        -e "s/{{HELD_MS}}/$held_ms/g" \
        -e "s/{{ALONE_MS}}/$alone_ms/g" \
        -e "s/{{STACK_DELAY_MS}}/$stack_delay_ms/g" \
        -e "s|{{LAZY_SUFFIX}}|$lazy_suffix|g" \
        -e "s|{{STREAK_SUFFIX}}|$streak_suffix|g" \
        -e "s|{{HYPER_CONDITION}}|$hyper_condition|g" \
        "$HRM_TEMPLATE"
}

# ============================================================================
# Build process
# ============================================================================
RULES_JSON="[]"

# Add rules 00-02
for rule_file in "$SRC_DIR/rules"/0[0-2]-*.json; do
    [[ -f "$rule_file" ]] || continue
    echo "  Adding: $(basename "$rule_file")"
    rule=$(add_device_condition < "$rule_file")
    RULES_JSON=$(echo "$RULES_JSON" | jq --argjson r "$rule" '. + [$r]')
done

# Generate HRM rules (03-10)
order=3
for config in "${HRM_CONFIG[@]}"; do
    IFS='|' read -r key_code modifier finger hand streak held alone stack hyper <<< "$config"
    key_display="$key_code"; [[ "$key_code" == "semicolon" ]] && key_display=";"
    printf "  Generating: %02d-hrm-%s-%s.json\n" "$order" "$hand" "$key_display"
    
    rule=$(generate_hrm_rule "$key_code" "$modifier" "$finger" "$hand" "$streak" "$held" "$alone" "$stack" "$hyper" | add_device_condition)
    RULES_JSON=$(echo "$RULES_JSON" | jq --argjson r "$rule" '. + [$r]')
    ((order++))
done

# Add rules 11+
for rule_file in "$SRC_DIR/rules"/1[1-9]-*.json "$SRC_DIR/rules"/[2-9][0-9]-*.json; do
    [[ -f "$rule_file" ]] || continue
    filename=$(basename "$rule_file")
    echo "  Adding: $filename"
    
    if is_all_devices_rule "$filename"; then
        rule=$(cat "$rule_file")
    else
        rule=$(add_device_condition < "$rule_file")
    fi
    RULES_JSON=$(echo "$RULES_JSON" | jq --argjson r "$rule" '. + [$r]')
done

# Merge into base.json
FINAL_JSON=$(jq --argjson rules "$RULES_JSON" '.profiles[0].complex_modifications.rules = $rules' "$SRC_DIR/base.json")
echo "$FINAL_JSON" > "$OUTPUT_FILE"

# Validate
if jq empty "$OUTPUT_FILE" 2>/dev/null; then
    rule_count=$(echo "$FINAL_JSON" | jq '.profiles[0].complex_modifications.rules | length')
    line_count=$(wc -l < "$OUTPUT_FILE" | tr -d ' ')
    echo -e "\nSuccess! Built $OUTPUT_FILE\n  - $rule_count rules\n  - $line_count lines"
else
    echo "Error: Generated invalid JSON!"
    exit 1
fi
