# Configure OpenCode - Configuration Management Task

## Purpose
Comprehensive task for managing OpenCode configuration, including agent creation, MCP setup, LSP configuration, and organizational structure management.

## Task Categories

### 1. Agent Management
- **Create New Agent**: Design and implement new agents following established patterns
- **Update Existing Agent**: Modify agent capabilities and configurations
- **Agent Organization**: Maintain proper agent structure and documentation
- **AGENTS.md Management**: Keep ecosystem documentation updated and concise

### 2. Configuration Management
- **Global Config**: Manage `~/.config/opencode/opencode.json`
- **Project Config**: Handle project-specific `./.opencode/opencode.json`
- **Schema Validation**: Ensure all configurations follow OpenCode schema
- **Configuration Optimization**: Optimize settings for performance and usability

### 3. MCP Integration
- **Add MCP Server**: Configure new local or remote MCP servers
- **MCP Troubleshooting**: Diagnose and resolve MCP integration issues
- **Environment Setup**: Configure MCP environment variables and settings
- **MCP Testing**: Validate MCP server functionality

### 4. LSP & Formatter Setup
- **Language Server Configuration**: Set up LSP servers for development languages
- **Formatter Integration**: Configure code formatters and their settings
- **Development Environment**: Optimize LSP/formatter settings for workflows
- **Custom LSP Setup**: Add support for custom or specialized language servers

### 5. Organizational Structure
- **Folder Management**: Create and maintain organized folder structures
- **File Organization**: Ensure proper separation of concerns
- **Structure Evolution**: Plan and implement structural improvements
- **Resource Management**: Organize agents, tasks, templates, workflows

## Configuration Patterns

### Agent Creation Pattern
```markdown
---
description: Brief agent description
model: anthropic/claude-sonnet-4-20250514
tools:
  write: true
  edit: true
  bash: false
---

# Agent Name - Role Description

Agent implementation following established patterns...
```

### MCP Configuration Pattern
```json
{
  "mcp": {
    "server-name": {
      "type": "local|remote",
      "command": ["command", "args"],
      "enabled": true,
      "environment": {
        "ENV_VAR": "value"
      }
    }
  }
}
```

### LSP Configuration Pattern
```json
{
  "lsp": {
    "language": {
      "command": ["language-server", "--stdio"],
      "extensions": [".ext"],
      "initialization": {
        "settings": {}
      }
    }
  }
}
```

## Execution Guidelines

### Pre-Task Analysis
1. **Understand Requirements**: Analyze the specific configuration need
2. **Review Current Setup**: Examine existing configuration and structure
3. **Plan Changes**: Design the configuration changes needed
4. **Validate Approach**: Ensure changes align with best practices

### Implementation Process
1. **Create/Modify Files**: Implement the configuration changes
2. **Validate Configuration**: Ensure schema compliance and functionality
3. **Test Changes**: Verify that changes work as expected
4. **Update Documentation**: Update AGENTS.md and related documentation
5. **Organize Structure**: Maintain proper file and folder organization

### Post-Task Validation
1. **Schema Compliance**: Verify all configurations follow OpenCode schema
2. **Functionality Testing**: Test that new configurations work properly
3. **Documentation Update**: Ensure documentation is current and accurate
4. **Structure Validation**: Confirm proper organization and structure

## Common Configuration Tasks

### Creating a New Agent
1. Analyze agent requirements and scope
2. Choose appropriate model and tool access
3. Create agent file with proper YAML frontmatter
4. Implement agent content following patterns
5. Update AGENTS.md with new agent (keep concise)
6. Test agent functionality

### Adding MCP Server
1. Identify MCP server requirements
2. Configure server in opencode.json
3. Set up environment variables if needed
4. Test MCP server integration
5. Document server purpose and usage

### Setting up LSP
1. Identify language server needs
2. Configure LSP server in opencode.json
3. Set up initialization options
4. Configure associated formatter
5. Test language server functionality

### Organizing Structure
1. Assess current organization
2. Plan structural improvements
3. Create new folders as needed
4. Move/organize existing files
5. Update references and documentation

## Quality Standards

### Configuration Quality
- All configurations must be schema-compliant
- Use appropriate models for agent complexity
- Configure minimal necessary tool access
- Include clear descriptions and documentation

### Organizational Quality
- Maintain separation of concerns
- Ensure reusability across components
- Support scalability and future expansion
- Follow established naming conventions

### Documentation Quality
- Keep AGENTS.md concise but comprehensive
- Ensure all agents are properly documented
- Maintain clear organizational structure
- Support git-based change tracking

## Integration Points

### BMad Methodology
- Support BMad workflow integration
- Maintain BMad organizational patterns
- Enable BMad quality processes
- Facilitate BMad agent coordination

### Development Workflow
- Integrate with development tools
- Support project-specific configurations
- Enable team collaboration features
- Maintain development environment optimization

### Quality Assurance
- Implement configuration validation
- Support testing and verification
- Maintain quality standards
- Enable continuous improvement

## Example Usage Scenarios

### Scenario 1: Create Code Review Agent
```
Task: Create a code-reviewer agent that focuses on security and performance
Steps:
1. Design agent with appropriate model and restricted tools
2. Create agent file with security-focused prompt
3. Configure tools to prevent code modification
4. Update AGENTS.md with new agent
5. Test agent functionality
```

### Scenario 2: Add Database MCP Server
```
Task: Add MCP server for database operations
Steps:
1. Configure database MCP server in opencode.json
2. Set up database connection environment variables
3. Test MCP server connectivity
4. Document server capabilities
5. Validate integration with existing workflow
```

### Scenario 3: Setup Python Development Environment
```
Task: Configure LSP and formatter for Python development
Steps:
1. Configure pylsp language server
2. Set up black formatter
3. Configure initialization options for optimal settings
4. Test language server and formatter functionality
5. Document configuration for team use
```

## Success Criteria

### Configuration Success
- All configurations are schema-compliant
- New configurations work as expected
- Performance is optimized
- Security considerations are addressed

### Organizational Success
- Structure supports easy navigation
- Components are properly organized
- Reusability is maximized
- Scalability is maintained

### Documentation Success
- AGENTS.md is updated and concise
- All changes are properly documented
- Team can understand and use configurations
- Git history provides clear change tracking
