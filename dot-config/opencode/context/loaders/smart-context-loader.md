# Smart Context Loader Implementation

## Context Loading Logic

### Pre-Loading Context Check
Before loading any context, agents should use this pattern:

```markdown
<conditional-block context-check="context-name">
IF [context-name] already loaded in current context:
  SKIP: Re-reading [context-name]
  NOTE: "Using [context-name] already in context"
ELSE:
  READ: [context-file-path]
</conditional-block>
```

### Project Type Detection
Use these patterns to detect project type and load appropriate context:

```yaml
detection_patterns:
  web_application:
    files: ["package.json", "src/", "public/", "index.html"]
    keywords: ["react", "vue", "angular", "svelte"]
    context_load:
      - "standards/coding/style-guides-lite.md"
      - "standards/security/secure-coding.md"
      - "products/web-apps/patterns.md"
  
  api_service:
    files: ["api/", "routes/", "controllers/", "openapi.yaml"]
    keywords: ["express", "fastapi", "rails", "django"]
    context_load:
      - "standards/coding/style-guides-lite.md"
      - "standards/security/secure-coding.md"
      - "products/apis/patterns.md"
```

### Context Loading Priority
1. **Always Load**: BMad methodology (lite version)
2. **Project-Specific**: Based on detected project type
3. **Task-Specific**: Based on current task requirements
4. **On-Demand**: Additional context as needed

### Smart Loading Implementation

#### For Main Agents
```markdown
## Context Loading Strategy

<conditional-block context-check="bmad-methodology">
IF BMad methodology already loaded:
  SKIP: Re-reading BMad methodology
ELSE:
  READ: standards/bmad/methodology-lite.md
</conditional-block>

<conditional-block context-check="project-detection">
IF project type already detected:
  USE: Existing project context
ELSE:
  DETECT: Project type using file patterns
  LOAD: Appropriate product context
</conditional-block>
```

#### For Subagents
```markdown
## Subagent Context Loading

<conditional-block context-check="specialized-context">
IF specialized context for [subagent-role] already loaded:
  SKIP: Re-reading specialized context
ELSE:
  READ: Relevant specialized context files
</conditional-block>
```

## Context Optimization Patterns

### Lite File Usage
- Use `-lite.md` versions for frequently accessed content
- Full versions only when detailed information needed
- Summarize large documents for context efficiency

### Selective Loading
- Load only relevant sections using grep
- Extract specific information rather than full files
- Cache processed context for reuse

### Context Validation
- Verify context relevance before loading
- Remove outdated or irrelevant context
- Monitor context usage and effectiveness

## Implementation Guidelines

### Agent Integration
1. Check existing context before loading new content
2. Use project detection to determine relevant context
3. Load lite versions when possible
4. Cache frequently used context

### Performance Optimization
- Target 60% token reduction through smart loading
- Maintain 90% context relevance
- Use conditional loading patterns consistently
- Monitor and optimize context usage

### Error Handling
- Graceful fallback when context unavailable
- Clear error messages for missing context
- Alternative context sources when needed
- Maintain functionality with reduced context