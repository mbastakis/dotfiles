# AgentOS Context Loading System

## Context Loading Strategy

### Three-Layer Architecture
The AgentOS context system implements a three-layer architecture for optimal context management:

1. **Standards Layer**: Global development standards and practices
2. **Products Layer**: Project-type specific patterns and configurations
3. **Specs Layer**: Feature-specific specifications and requirements

### Smart Loading Principles

#### Conditional Loading
```yaml
context_loading:
  standards:
    always_load: ["bmad/methodology", "coding/style-guides"]
    conditional:
      web_project: ["security/secure-coding", "performance/optimization"]
      api_project: ["apis/patterns", "security/secure-coding"]
      mobile_project: ["mobile/patterns", "performance/optimization"]
  
  products:
    detection: "auto"  # Auto-detect project type
    fallback: "web-apps"
    
  specs:
    source: "project_context"
    cache_duration: "1h"
```

#### Context Validation
Before loading context, validate:
- Is this context already loaded?
- Is this context relevant to the current task?
- Can we use a lite version instead?

### Loading Patterns

#### Lite File Strategy
For frequently accessed documents, maintain both full and lite versions:
- `methodology.md` - Complete BMad methodology
- `methodology-lite.md` - Essential BMad principles only

#### Context Checking
```markdown
<conditional-block context-check="bmad-methodology">
IF BMad methodology already loaded in current context:
  SKIP: Re-reading methodology
  NOTE: "Using BMad methodology already in context"
ELSE:
  READ: standards/bmad/methodology-lite.md
</conditional-block>
```

## Implementation Guidelines

### Agent Integration
Agents should:
1. Check existing context before loading new content
2. Load only relevant context for current task
3. Use lite versions when full context isn't needed
4. Cache frequently used context

### Performance Optimization
- **Context Caching**: Cache loaded context for reuse
- **Selective Loading**: Load only necessary sections
- **Lazy Loading**: Load context on demand
- **Context Cleanup**: Remove unused context periodically

### Error Handling
- Graceful fallback when context unavailable
- Clear error messages for missing context
- Alternative context sources when primary unavailable