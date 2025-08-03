# Documentation Formatting Standards

## Overview
This document defines the formatting standards for all OpenCode documentation to ensure consistency, readability, and maintainability across the entire configuration.

## File Structure Standards

### YAML Frontmatter (for Agent Files)
```yaml
---
description: Brief description of the agent's purpose and when to use it
model: anthropic/claude-sonnet-4-20250514
context_layers:
  standards: ["bmad", "documentation"]
  products: ["conditional:project_type"]
  specs: ["conditional:active_project"]
subagents:
  - name: "subagent-name"
    role: "role_description"
    auto_spawn: ["condition1", "condition2"]
tools:
  read: true
  write: true
  bash: true
quality_gates:
  - "gate_name"
agentos_integration: true
---
```

### Markdown Structure
```markdown
# Main Title (H1) - Only one per document

## Section Title (H2) - Primary sections

### Subsection Title (H3) - Secondary sections

#### Detail Section (H4) - Detailed breakdowns

##### Minor Section (H5) - Minor details (use sparingly)
```

## Heading Standards

### Capitalization
- **Title Case**: Use for H1 and H2 headings
- **Sentence case**: Use for H3, H4, H5 headings

### Examples
```markdown
# OpenCode Configuration Guide (H1 - Title Case)
## Agent Ecosystem Overview (H2 - Title Case)
### Core development agents (H3 - Sentence case)
#### Business analyst configuration (H4 - Sentence case)
```

## Emoji Usage Standards

### Consistent Emoji Patterns
- 🎭 **BMad Master** - Universal executor
- 📊 **Business Analyst** - Requirements and analysis
- 🚀 **Product Manager** - Product strategy
- 👤 **Product Owner** - Backlog management
- 🏗️ **System Architect** - Technical architecture
- 💻 **Senior Developer** - Implementation
- 🎨 **UX Designer** - User experience
- ✅ **Quality Assurance** - Testing and validation
- 🔄 **Scrum Master** - Process facilitation
- 🔍 **Deep Researcher** - Advanced research
- ⚙️ **OpenCode Configurator** - Configuration management
- 📋 **Agent Lister** - Quick reference

### Status Indicators
- ✅ **Completed/Working** - Green checkmark
- 🔄 **In Progress** - Blue refresh
- ❌ **Failed/Missing** - Red X
- ⚠️ **Warning/Attention** - Yellow warning
- 🎯 **Target/Goal** - Bullseye
- 🚀 **Enhancement/New** - Rocket

### Priority Indicators
- 🔥 **Critical** - Fire
- ⚡ **High Priority** - Lightning
- 📈 **Medium Priority** - Chart
- 💡 **Low Priority/Idea** - Light bulb

## Code Block Standards

### Language Specification
Always specify the language for syntax highlighting:

```yaml
# YAML configuration
key: value
```

```bash
# Bash commands
command --option value
```

```markdown
# Markdown examples
## Heading
```

### Command Examples
```bash
# Good - with description
@bmad-master I want to start a new fullstack project

# Good - with expected outcome
@context-primer Analyze this project and provide development context
# Returns: Comprehensive project analysis and orientation
```

## Link Standards

### Internal Links
- Use relative paths for internal documentation
- Include descriptive link text
- Verify all links are functional

```markdown
# Good
See [BMad methodology documentation](knowledge/bmad-kb.md) for details

# Bad
See [here](knowledge/bmad-kb.md) for details
```

### External Links
- Use full URLs for external resources
- Include link descriptions when helpful

```markdown
# Good
For more information, see [OpenCode documentation](https://opencode.ai/docs)

# Good with description
See the [Anthropic Claude documentation](https://docs.anthropic.com) for model details
```

## List Standards

### Unordered Lists
- Use `-` for primary list items
- Use `  -` (2 spaces) for nested items
- Use `    -` (4 spaces) for third-level nesting

```markdown
- Primary item
  - Secondary item
    - Tertiary item
- Another primary item
```

### Ordered Lists
- Use `1.` for all items (auto-numbering)
- Use consistent indentation for nested items

```markdown
1. First step
   1. Sub-step
   2. Another sub-step
2. Second step
3. Third step
```

## Table Standards

### Basic Table Format
```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

### Alignment
- Left-align text columns
- Right-align numeric columns
- Center-align status indicators

```markdown
| Agent Name | Priority | Status |
|:-----------|:---------|:------:|
| BMad Master| High     |   ✅   |
| Business Analyst | Medium | 🔄 |
```

## Content Standards

### Descriptions
- Keep agent descriptions concise (1-2 lines)
- Focus on "what" and "when to use"
- Include usage examples

### Usage Examples
- Provide clear, actionable examples
- Use realistic scenarios
- Include expected outcomes when helpful

```markdown
#### Usage Example
```bash
@business-analyst Gather requirements for user authentication feature
# Expected: Comprehensive requirements document with stakeholder analysis
```

### Cross-References
- Link to related documentation
- Provide context for references
- Use descriptive link text

## File Naming Standards

### Consistency Rules
- Use kebab-case for all file names
- Include descriptive prefixes when appropriate
- Use consistent suffixes

```
# Good
bmad-methodology.md
context-optimization.md
performance-monitoring.md

# Bad
BMadMethodology.md
context_optimization.md
performanceMonitoring.md
```

## Quality Checklist

Before publishing any documentation, verify:

- [ ] Consistent heading capitalization
- [ ] Proper emoji usage according to standards
- [ ] All code blocks have language specification
- [ ] All internal links are functional
- [ ] Consistent list formatting
- [ ] Proper table alignment
- [ ] Descriptive link text
- [ ] Consistent file naming
- [ ] No spelling or grammar errors
- [ ] Appropriate use of formatting elements

## Maintenance

### Regular Reviews
- Review documentation quarterly for consistency
- Update standards as needed
- Ensure all documentation follows current standards

### Automated Checks
- Use linting tools where possible
- Implement automated link checking
- Monitor for formatting consistency

This document should be referenced when creating or updating any documentation in the OpenCode configuration.