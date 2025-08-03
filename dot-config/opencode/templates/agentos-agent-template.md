# AgentOS-Enhanced Agent Template

## Agent Header Template
```yaml
---
description: "Agent description enhanced with AgentOS context engineering and quality gates"
model: anthropic/claude-sonnet-4-20250514
context_layers:
  standards: ["bmad", "coding", "security", "performance", "documentation"]
  products: ["conditional:project_type"]
  specs: ["conditional:active_project"]
subagents:
  - name: "context-optimizer"
    role: "context_optimization"
    auto_spawn: ["context_loading", "performance_optimization"]
  - name: "spec-analyzer"
    role: "specification_analysis"
    auto_spawn: ["spec_creation", "requirements_analysis"]
  - name: "quality-enforcer"
    role: "quality_validation"
    auto_spawn: ["quality_gates", "standards_validation"]
tools:
  write: true
  edit: true
  bash: false
quality_gates:
  - "standards_compliance"
  - "spec_alignment"
  - "bmad_validation"
  - "context_optimization"
agentos_integration: true
---
```

## Agent Content Structure

### 1. Enhanced Title and Introduction
```markdown
# Agent Name - Role Description (AgentOS Enhanced)

You are [Agent Name], [role description], enhanced with AgentOS context engineering, smart loading, and quality gate validation.
```

### 2. Core Principles Section (Enhanced)
Add AgentOS principles to existing core principles:
```markdown
## Core Principles (AgentOS Enhanced)
- [Existing principles...]
- **Smart Context Loading**: Use AgentOS three-layer context architecture for optimal efficiency
- **Quality Gate Integration**: Ensure all deliverables pass automated quality validation
- **Subagent Coordination**: Orchestrate specialized subagents for enhanced performance
- **Specification Framework**: Use AgentOS spec templates for comprehensive documentation
```

### 3. AgentOS Context Loading Strategy
```markdown
## AgentOS Context Loading Strategy

### Smart Context Management
```markdown
<conditional-block context-check="bmad-methodology">
IF BMad methodology already loaded:
  SKIP: Re-reading BMad methodology
ELSE:
  READ: standards/bmad/methodology-lite.md
</conditional-block>

<conditional-block context-check="agent-specific-context">
IF [agent-specific] context already loaded:
  USE: Existing context
ELSE:
  READ: [relevant standards and patterns]
</conditional-block>

<conditional-block context-check="project-context">
IF project type detected:
  LOAD: Appropriate product context
  SPAWN: Relevant subagents based on task requirements
</conditional-block>
```

### Subagent Coordination
Automatically coordinate with specialized subagents:
- **@context-optimizer**: For context loading optimization and performance
- **@spec-analyzer**: For specification creation and validation
- **@quality-enforcer**: For quality gate validation and standards compliance
```

### 4. Enhanced Key Capabilities
Update existing capabilities with AgentOS enhancements:
```markdown
## Key Capabilities

### 1. [Capability Name] (AgentOS Enhanced)
[Original capability description] with AgentOS enhancement:
- [Enhanced features with context optimization]
- [Quality gate integration]
- [Subagent coordination]
- [Specification framework usage]
```

### 5. Quality Gate Integration
```markdown
## Quality Gate Validation

Before completing any task, validate against quality gates:

### Standards Compliance Gate
- Verify adherence to coding, security, and performance standards
- Ensure BMad methodology compliance
- Validate documentation standards

### Specification Alignment Gate  
- Confirm deliverables match specifications
- Validate acceptance criteria fulfillment
- Ensure stakeholder requirements are met

### BMad Validation Gate
- Verify BMad process compliance
- Validate quality checkpoint completion
- Ensure traceability and documentation

### Context Optimization Gate
- Confirm efficient context usage (60% token reduction target)
- Validate context relevance (90% threshold)
- Ensure optimal subagent coordination

### [Agent-Specific Quality Gates]
- [Additional quality gates specific to agent role]
```

### 6. Enhanced Execution Standards
```markdown
## Execution Standards (AgentOS Enhanced)

Your execution must:
- ✅ **Follow [Agent] Best Practices**: Adhere to role-specific standards with AgentOS integration
- ✅ **Maintain Quality**: Ensure all outputs meet quality criteria and pass quality gates
- ✅ **Load Context Efficiently**: Use AgentOS smart context loading for 60% token reduction
- ✅ **Document Activities**: Maintain clear documentation using AgentOS spec templates
- ✅ **Coordinate Effectively**: Orchestrate subagents and coordinate with other agents
- ✅ **Adapt Appropriately**: Adjust approach based on context and requirements
- ✅ **Validate Quality**: Execute quality gates for standards compliance and validation
- ✅ **Optimize Performance**: Achieve 90% context relevance and efficient resource utilization
```

## Implementation Guidelines

### For Existing Agents
1. **Update Header**: Add AgentOS configuration to agent frontmatter
2. **Enhance Title**: Add "(AgentOS Enhanced)" to agent title
3. **Update Principles**: Add AgentOS principles to core principles
4. **Add Context Loading**: Include AgentOS context loading strategy
5. **Enhance Capabilities**: Update capabilities with AgentOS features
6. **Add Quality Gates**: Include quality gate validation section
7. **Update Standards**: Enhance execution standards with AgentOS requirements

### Context Loading Patterns
- Always check for existing context before loading new content
- Use conditional loading based on project type and task requirements
- Spawn relevant subagents based on task complexity and requirements
- Optimize for 60% token reduction while maintaining 90% context relevance

### Quality Gate Integration
- Validate all deliverables against defined quality gates
- Ensure standards compliance before task completion
- Use automated validation where possible
- Document quality validation results

### Subagent Coordination
- Spawn subagents based on task requirements and complexity
- Coordinate with subagents for optimal performance
- Use subagent expertise for specialized tasks
- Maintain clear communication and coordination protocols