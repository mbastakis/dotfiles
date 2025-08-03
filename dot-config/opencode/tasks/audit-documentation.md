# Documentation Audit and Standardization Task

## Purpose
Systematically audit and standardize all documentation in the OpenCode configuration according to the formatting standards.

## Audit Checklist

### File Structure Audit
- [ ] All agent files have proper YAML frontmatter
- [ ] Consistent heading hierarchy (H1 → H2 → H3 → H4)
- [ ] Proper file naming conventions (kebab-case)

### Content Consistency Audit
- [ ] Consistent emoji usage across all files
- [ ] Standardized agent descriptions
- [ ] Proper code block language specification
- [ ] Functional internal links
- [ ] Consistent list formatting

### Quality Standards Audit
- [ ] No spelling or grammar errors
- [ ] Consistent capitalization in headings
- [ ] Proper table formatting and alignment
- [ ] Descriptive link text (no "here" or "click here")

## Common Issues Found

### Heading Inconsistencies
```markdown
# Fix These
## core agents (should be: Core Agents)
### Business Analyst Agent (should be: Business analyst agent)

# To This
## Core Agents
### Business analyst agent
```

### Emoji Inconsistencies
```markdown
# Fix These
🔍 **Deep Researcher** (inconsistent with other research agents)
📊 **Business Analyst** (correct)

# Standardize To
🔍 **Deep Researcher** (research/analysis)
📊 **Business Analyst** (business/analysis)
```

### Link Issues
```markdown
# Fix These
[here](knowledge/bmad-kb.md)
[click here for details](agentos-config.yaml)

# To This
[BMad methodology documentation](knowledge/bmad-kb.md)
[AgentOS configuration details](agentos-config.yaml)
```

## Standardization Actions

### 1. Agent File Standardization
- Ensure all agent files follow the YAML frontmatter template
- Standardize agent descriptions to 1-2 lines
- Add consistent usage examples

### 2. Documentation Cross-References
- Update all internal links to use descriptive text
- Verify all links are functional
- Add missing cross-references where helpful

### 3. Formatting Consistency
- Standardize heading capitalization
- Ensure consistent emoji usage
- Fix table formatting and alignment

### 4. Content Quality
- Review all content for clarity and accuracy
- Remove redundant information
- Ensure consistent terminology usage

## Implementation Priority

### High Priority
1. Fix broken internal links
2. Standardize agent descriptions
3. Ensure consistent emoji usage
4. Fix heading capitalization

### Medium Priority
1. Improve table formatting
2. Add missing cross-references
3. Standardize code block formatting
4. Review content for clarity

### Low Priority
1. Minor formatting improvements
2. Additional cross-references
3. Enhanced examples
4. Style refinements

## Validation Process

### Automated Checks
- Link validation
- Spelling and grammar check
- Formatting consistency check

### Manual Review
- Content accuracy review
- Cross-reference validation
- User experience assessment

## Success Metrics

### Consistency Score
- Target: 95% consistency across all documentation
- Measure: Automated formatting checks
- Review: Monthly consistency audits

### Link Health
- Target: 100% functional internal links
- Measure: Automated link checking
- Review: Weekly link validation

### User Experience
- Target: Clear, navigable documentation
- Measure: User feedback and usage patterns
- Review: Quarterly UX assessment

This task should be executed systematically to ensure all OpenCode documentation meets the established standards.