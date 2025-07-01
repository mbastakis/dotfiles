# Create AI Documentation File

Create a new AI documentation file in your dotfiles ai_docs directory.

## Usage
`/create_ai_docs filename`

## Arguments
**filename** (required): Name of the AI docs file to create (without .md extension)

---

$ARGUMENTS_PROCESSING

# Processing Arguments

!if [ -z "$ARGUMENTS" ]; then
    echo "## Error: Filename is required"
    echo ""
    echo "Usage: /create_ai_docs filename"
    echo "Example: /create_ai_docs new_framework_documentation"
    echo ""
    echo "## Existing AI docs files:"
    ls ~/ai_docs/ 2>/dev/null | grep "\.md$" | sed 's/^/- /' || echo "No AI docs files found"
else
    FILENAME="$ARGUMENTS"
    
    # Remove .md extension if provided
    FILENAME=$(echo "$FILENAME" | sed 's/\.md$//')
    
    # Check if file already exists
    if [ -f ~/dev/dotfiles/config/ai_docs/"${FILENAME}.md" ]; then
        echo "## File already exists: ${FILENAME}.md"
        echo ""
        echo "Contents:"
        echo "---"
        cat ~/dev/dotfiles/config/ai_docs/"${FILENAME}.md"
    else
        # Create the file with template
        cat > ~/dev/dotfiles/config/ai_docs/"${FILENAME}.md" << 'EOF'
# [TECHNOLOGY/FRAMEWORK NAME] Documentation

## Overview
Brief description of the technology, framework, or tool.

## Key Concepts
- Concept 1: Description
- Concept 2: Description
- Concept 3: Description

## Installation & Setup
```bash
# Installation commands
```

## Basic Usage
```[language]
// Basic usage examples
```

## Common Patterns
### Pattern 1
Description and example

### Pattern 2
Description and example

## Best Practices
- Best practice 1
- Best practice 2
- Best practice 3

## Common Issues & Solutions
### Issue 1
**Problem**: Description of the problem
**Solution**: How to solve it

### Issue 2
**Problem**: Description of the problem
**Solution**: How to solve it

## Resources
- [Official Documentation](https://example.com)
- [Tutorial](https://example.com)
- [GitHub Repository](https://example.com)

## Notes
Additional notes and considerations for AI assistance.
EOF
        
        echo "## Created new AI docs file: ${FILENAME}.md"
        echo ""
        echo "File location: ~/dev/dotfiles/config/ai_docs/${FILENAME}.md"
        echo "Also accessible via: ~/ai_docs/${FILENAME}.md"
        echo ""
        echo "Template content has been added. You can now edit the file to add your documentation details."
    fi
fi