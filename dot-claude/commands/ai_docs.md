# AI Documentation Reader

Access and read AI documentation files from your global ai_docs directory.

## Usage
- `/ai_docs` - List all available AI documentation files
- `/ai_docs filename` - Read a specific AI docs file (supports partial matching)

## Arguments
**filename** (optional): Name or partial name of the AI docs file to read

---

# Available AI Documentation Files

!ls ~/ai_docs/ 2>/dev/null | grep -v "^l" | grep "\.md$" | sed 's/\.md$//' || echo "No AI docs files found"

---

$ARGUMENTS_PROCESSING

# Processing Arguments

!if [ -z "$ARGUMENTS" ]; then
    echo "## Available AI Documentation Files:"
    ls ~/ai_docs/ 2>/dev/null | grep "\.md$" | sed 's/^/- /' || echo "No AI docs files found"
    echo ""
    echo "Usage: /ai_docs filename"
    echo "Example: /ai_docs bubbletea_documentation"
else
    FILENAME="$ARGUMENTS"
    
    # Try exact match first
    if [ -f ~/ai_docs/"${FILENAME}.md" ]; then
        echo "## Reading: ${FILENAME}.md"
        echo ""
        cat ~/ai_docs/"${FILENAME}.md"
    elif [ -f ~/ai_docs/"${FILENAME}" ]; then
        echo "## Reading: ${FILENAME}"
        echo ""
        cat ~/ai_docs/"${FILENAME}"
    else
        # Try partial matching
        MATCHES=$(ls ~/ai_docs/ 2>/dev/null | grep -i "${FILENAME}" || echo "")
        if [ -n "$MATCHES" ]; then
            MATCH_COUNT=$(echo "$MATCHES" | wc -l | tr -d ' ')
            if [ "$MATCH_COUNT" -eq 1 ]; then
                MATCHED_FILE="$MATCHES"
                echo "## Found match: ${MATCHED_FILE}"
                echo ""
                cat ~/ai_docs/"${MATCHED_FILE}"
            else
                echo "## Multiple matches found for '${FILENAME}':"
                echo "$MATCHES" | sed 's/^/- /'
                echo ""
                echo "Please be more specific."
            fi
        else
            echo "## No AI docs file found matching '${FILENAME}'"
            echo ""
            echo "Available files:"
            ls ~/ai_docs/ 2>/dev/null | grep "\.md$" | sed 's/^/- /' || echo "No AI docs files found"
        fi
    fi
fi