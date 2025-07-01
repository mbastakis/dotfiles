# Specs File Reader

Access and read specification files from your global specs directory.

## Usage
- `/specs` - List all available specs files
- `/specs filename` - Read a specific specs file (supports partial matching)

## Arguments
**filename** (optional): Name or partial name of the specs file to read

---

# Available Specs Files

!ls ~/specs/ 2>/dev/null | grep -v "^l" | grep "\.md$" | sed 's/\.md$//' || echo "No specs files found"

---

$ARGUMENTS_PROCESSING

# Processing Arguments

!if [ -z "$ARGUMENTS" ]; then
    echo "## Available Specs Files:"
    ls ~/specs/ 2>/dev/null | grep "\.md$" | sed 's/^/- /' || echo "No specs files found"
    echo ""
    echo "Usage: /specs filename"
    echo "Example: /specs implement_todo"
else
    FILENAME="$ARGUMENTS"
    
    # Try exact match first
    if [ -f ~/specs/"${FILENAME}.md" ]; then
        echo "## Reading: ${FILENAME}.md"
        echo ""
        cat ~/specs/"${FILENAME}.md"
    elif [ -f ~/specs/"${FILENAME}" ]; then
        echo "## Reading: ${FILENAME}"
        echo ""
        cat ~/specs/"${FILENAME}"
    else
        # Try partial matching
        MATCHES=$(ls ~/specs/ 2>/dev/null | grep -i "${FILENAME}" || echo "")
        if [ -n "$MATCHES" ]; then
            MATCH_COUNT=$(echo "$MATCHES" | wc -l | tr -d ' ')
            if [ "$MATCH_COUNT" -eq 1 ]; then
                MATCHED_FILE="$MATCHES"
                echo "## Found match: ${MATCHED_FILE}"
                echo ""
                cat ~/specs/"${MATCHED_FILE}"
            else
                echo "## Multiple matches found for '${FILENAME}':"
                echo "$MATCHES" | sed 's/^/- /'
                echo ""
                echo "Please be more specific."
            fi
        else
            echo "## No specs file found matching '${FILENAME}'"
            echo ""
            echo "Available files:"
            ls ~/specs/ 2>/dev/null | grep "\.md$" | sed 's/^/- /' || echo "No specs files found"
        fi
    fi
fi