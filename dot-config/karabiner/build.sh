#!/usr/bin/env bash
# Build karabiner.json from modular source files
# Usage: ./build.sh
#
# This script merges base.json and all rule files from src/rules/
# into the final karabiner.json that Karabiner-Elements uses.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
OUTPUT_FILE="$SCRIPT_DIR/karabiner.json"

# Check for jq
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed."
    echo "Install with: brew install jq"
    exit 1
fi

# Verify source files exist
if [[ ! -f "$SRC_DIR/base.json" ]]; then
    echo "Error: $SRC_DIR/base.json not found"
    exit 1
fi

if [[ ! -d "$SRC_DIR/rules" ]]; then
    echo "Error: $SRC_DIR/rules directory not found"
    exit 1
fi

echo "Building karabiner.json..."

# Start with base.json
BASE_JSON=$(cat "$SRC_DIR/base.json")

# Collect all rules from rule files (sorted by filename for predictable order)
RULES_JSON="[]"
for rule_file in "$SRC_DIR/rules"/*.json; do
    if [[ -f "$rule_file" ]]; then
        echo "  Adding: $(basename "$rule_file")"
        # Each rule file contains a single rule object, append it to the array
        RULES_JSON=$(echo "$RULES_JSON" | jq --slurpfile rule "$rule_file" '. + [$rule[0]]')
    fi
done

# Merge rules into base.json at profiles[0].complex_modifications.rules
FINAL_JSON=$(echo "$BASE_JSON" | jq --argjson rules "$RULES_JSON" '
    .profiles[0].complex_modifications.rules = $rules
')

# Write output
echo "$FINAL_JSON" > "$OUTPUT_FILE"

# Validate the output is valid JSON
if jq empty "$OUTPUT_FILE" 2>/dev/null; then
    RULE_COUNT=$(echo "$FINAL_JSON" | jq '.profiles[0].complex_modifications.rules | length')
    LINE_COUNT=$(wc -l < "$OUTPUT_FILE" | tr -d ' ')
    echo ""
    echo "Success! Built $OUTPUT_FILE"
    echo "  - $RULE_COUNT rules"
    echo "  - $LINE_COUNT lines"
else
    echo "Error: Generated invalid JSON!"
    exit 1
fi
