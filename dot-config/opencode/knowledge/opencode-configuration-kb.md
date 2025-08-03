# OpenCode Configuration Knowledge Base

## Latest OpenCode Features & Configuration (v0.3.113+)

### Core Configuration Schema
```json
{
  "$schema": "https://opencode.ai/config.json",
  "theme": "system",
  "model": "anthropic/claude-sonnet-4-20250514",
  "small_model": "anthropic/claude-3-5-haiku-20241022",
  "autoupdate": true,
  "share": "manual",
  "mode": {},
  "agent": {},
  "mcp": {},
  "formatter": {},
  "lsp": {},
  "instructions": [],
  "permission": {},
  "keybinds": {},
  "experimental": {}
}
```

## MCP (Model Context Protocol) Configuration

### Local MCP Server Examples
```json
{
  "mcp": {
    "snap-happy": {
      "type": "local",
      "command": ["npx", "@mariozechner/snap-happy"],
      "enabled": true,
      "environment": {
        "SNAP_HAPPY_SCREENSHOT_PATH": "${HOME}/Screenshots"
      }
    },
    "context7": {
      "type": "local",
      "command": ["npx", "-y", "@upstash/context7-mcp"],
      "enabled": true
    },
    "filesystem": {
      "type": "local",
      "command": ["npx", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"],
      "enabled": true
    },
    "brave-search": {
      "type": "local",
      "command": ["npx", "@modelcontextprotocol/server-brave-search"],
      "enabled": true,
      "environment": {
        "BRAVE_API_KEY": "{env:BRAVE_API_KEY}"
      }
    }
  }
}
```

### Remote MCP Server Examples
```json
{
  "mcp": {
    "remote-server": {
      "type": "remote",
      "url": "https://api.example.com/mcp",
      "enabled": true,
      "headers": {
        "Authorization": "Bearer {env:API_TOKEN}",
        "X-Custom-Header": "value"
      }
    }
  }
}
```

## LSP (Language Server Protocol) Configuration

### Built-in LSP Servers
```json
{
  "lsp": {
    "typescript": {
      "command": ["typescript-language-server", "--stdio"],
      "extensions": [".ts", ".tsx", ".js", ".jsx"],
      "initialization": {
        "preferences": {
          "includeInlayParameterNameHints": "all",
          "includeInlayVariableTypeHints": true,
          "includeInlayFunctionParameterTypeHints": true
        }
      }
    },
    "python": {
      "command": ["pylsp"],
      "extensions": [".py"],
      "initialization": {
        "settings": {
          "pylsp": {
            "plugins": {
              "pycodestyle": {"enabled": true},
              "pyflakes": {"enabled": true},
              "pylint": {"enabled": true}
            }
          }
        }
      }
    },
    "go": {
      "command": ["gopls"],
      "extensions": [".go"],
      "initialization": {
        "settings": {
          "gopls": {
            "analyses": {
              "unusedparams": true,
              "shadow": true
            },
            "staticcheck": true
          }
        }
      }
    },
    "rust": {
      "command": ["rust-analyzer"],
      "extensions": [".rs"],
      "initialization": {
        "settings": {
          "rust-analyzer": {
            "checkOnSave": {
              "command": "clippy"
            }
          }
        }
      }
    }
  }
}
```

## Formatter Configuration

### Built-in Formatters
```json
{
  "formatter": {
    "prettier": {
      "disabled": false,
      "command": ["npx", "prettier", "--write", "$FILE"],
      "extensions": [".js", ".ts", ".jsx", ".tsx", ".json", ".md", ".css", ".html"]
    },
    "black": {
      "disabled": false,
      "command": ["black", "$FILE"],
      "extensions": [".py"]
    },
    "gofmt": {
      "disabled": false,
      "command": ["gofmt", "-w", "$FILE"],
      "extensions": [".go"]
    },
    "rustfmt": {
      "disabled": false,
      "command": ["rustfmt", "$FILE"],
      "extensions": [".rs"]
    },
    "clang-format": {
      "disabled": false,
      "command": ["clang-format", "-i", "$FILE"],
      "extensions": [".c", ".cpp", ".h", ".hpp"]
    }
  }
}
```

## Agent Configuration Patterns

### JSON Agent Configuration
```json
{
  "agent": {
    "code-reviewer": {
      "description": "Reviews code for best practices and potential issues",
      "model": "anthropic/claude-sonnet-4-20250514",
      "temperature": 0.1,
      "prompt": "You are a code reviewer with expertise in security, performance, and maintainability...",
      "tools": {
        "write": false,
        "edit": false,
        "bash": false
      }
    },
    "documentation-writer": {
      "description": "Creates comprehensive technical documentation",
      "model": "anthropic/claude-sonnet-4-20250514",
      "prompt": "{file:./prompts/documentation.md}",
      "tools": {
        "write": true,
        "edit": true,
        "bash": false
      }
    }
  }
}
```

### Markdown Agent Configuration Template
```markdown
---
description: Brief description of the agent's role
model: anthropic/claude-sonnet-4-20250514
temperature: 0.7
tools:
  write: true
  edit: true
  bash: false
---

# Agent Name - Role Description

## Your Role & Identity
- **Style**: Define the agent's communication style
- **Focus**: Primary areas of expertise
- **Expertise**: Specific knowledge domains

## Core Capabilities
1. **Primary Function**: Main responsibility
2. **Secondary Functions**: Additional capabilities
3. **Integration**: How it works with other agents

## Working Guidelines
- Specific instructions for the agent
- Quality standards to maintain
- Integration patterns with other systems

## Example Usage
```
Example commands or interactions
```
```

## Mode Configuration

### Custom Modes
```json
{
  "mode": {
    "review": {
      "model": "anthropic/claude-sonnet-4-20250514",
      "temperature": 0.1,
      "prompt": "You are in review mode. Focus on analysis without making changes.",
      "tools": {
        "write": false,
        "edit": false,
        "bash": false
      }
    },
    "debug": {
      "model": "anthropic/claude-sonnet-4-20250514",
      "temperature": 0.3,
      "prompt": "{file:./mode/debug.md}",
      "tools": {
        "write": true,
        "edit": true,
        "bash": true
      }
    }
  }
}
```

## Permission System

### Granular Permissions
```json
{
  "permission": {
    "edit": "ask",
    "write": "allow",
    "bash": {
      "git push": "ask",
      "rm -rf": "deny",
      "npm install": "allow",
      "*": "ask"
    }
  }
}
```

## Variable Substitution

### Environment Variables
```json
{
  "model": "{env:OPENCODE_MODEL}",
  "mcp": {
    "server": {
      "environment": {
        "API_KEY": "{env:MY_API_KEY}"
      }
    }
  }
}
```

### File Content Substitution
```json
{
  "instructions": [
    "{file:./CONTRIBUTING.md}",
    "{file:./docs/guidelines.md}"
  ],
  "agent": {
    "custom": {
      "prompt": "{file:./prompts/custom-agent.md}"
    }
  }
}
```

## Configuration Hierarchy

1. **Custom config file** (via `OPENCODE_CONFIG` environment variable)
2. **Project-specific config** (`./opencode.json`)
3. **Global config** (`~/.config/opencode/opencode.json`)

## Best Practices

### Configuration Organization
- Use schema validation with `"$schema": "https://opencode.ai/config.json"`
- Separate global preferences from project-specific settings
- Use environment variables for sensitive data
- Leverage file substitution for reusable content

### Agent Creation
- Follow consistent naming conventions
- Use appropriate models for agent complexity
- Configure minimal necessary tool access
- Include clear descriptions and examples

### MCP Integration
- Test MCP servers before adding to configuration
- Use environment variables for API keys
- Enable/disable servers as needed
- Monitor MCP server performance

### LSP & Formatter Setup
- Configure LSP servers for all used languages
- Set up formatters to match project standards
- Use initialization options for optimal settings
- Test language server functionality

## Common Configuration Patterns

### Development Environment Setup
```json
{
  "lsp": {
    "typescript": {"command": ["typescript-language-server", "--stdio"]},
    "python": {"command": ["pylsp"]},
    "go": {"command": ["gopls"]}
  },
  "formatter": {
    "prettier": {"extensions": [".js", ".ts", ".json"]},
    "black": {"extensions": [".py"]},
    "gofmt": {"extensions": [".go"]}
  },
  "mcp": {
    "filesystem": {
      "type": "local",
      "command": ["npx", "@modelcontextprotocol/server-filesystem", "."]
    }
  }
}
```

### Security-Focused Configuration
```json
{
  "permission": {
    "edit": "ask",
    "bash": {
      "git": "allow",
      "npm": "allow",
      "rm": "ask",
      "*": "ask"
    }
  },
  "agent": {
    "security-reviewer": {
      "tools": {
        "write": false,
        "edit": false,
        "bash": false
      }
    }
  }
}
```

### Team Collaboration Setup
```json
{
  "instructions": [
    "{file:./CONTRIBUTING.md}",
    "{file:./.github/CODING_STANDARDS.md}"
  ],
  "formatter": {
    "prettier": {
      "command": ["npx", "prettier", "--config", "./.prettierrc", "--write", "$FILE"]
    }
  }
}
```

## Troubleshooting

### Common Issues
1. **MCP Server Not Working**: Check command path and environment variables
2. **LSP Not Starting**: Verify language server installation and command
3. **Formatter Failing**: Check formatter installation and file permissions
4. **Agent Not Loading**: Validate YAML frontmatter syntax
5. **Schema Validation Errors**: Ensure all required fields are present

### Debugging Tips
- Use `opencode --version` to check current version
- Validate JSON configuration with schema
- Test MCP servers independently
- Check OpenCode logs for error messages
- Verify file paths and permissions

## Latest Updates (v0.3.113)

### New Features
- Enhanced MCP integration with better error handling
- Improved bash tool output (includes stderr)
- Better configuration error messages
- Kimi K2 ⇄ Claude trajectory handoff support
- Attachment handling improvements

### Configuration Changes
- More robust MCP server configuration
- Enhanced permission system with wildcard patterns
- Improved LSP server customization
- Better formatter configuration options