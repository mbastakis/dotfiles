# Claude Code CLI Configuration

This directory contains the configuration for [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code), Anthropic's official CLI tool for AI-assisted coding.

## Files

- `.claude/settings.json` - Claude Code settings and permissions
- `.claude/commands/` - Custom commands for Claude Code
- `.mcp.json` - MCP (Model Context Protocol) server configurations

## MCP Tools

Claude Code is configured with the following MCP tools:

### Docker MCP Tools
- **Purpose**: Access to containerized MCP tools and services
- **Command**: `docker run -i --rm alpine/socat STDIO TCP:host.docker.internal:8811`
- **Requirements**: 
  - Docker Desktop running
  - MCP container accessible at `host.docker.internal:8811`

### Snap-happy Screenshot Tool
- **Purpose**: Cross-platform screenshot capture for AI assistance
- **Command**: `npx @mariozechner/snap-happy`
- **Functions**:
  - Take screenshots
  - Get last screenshot
  - List windows (macOS only)
- **Requirements**: 
  - Node.js and npm installed
  - Screen recording permissions on macOS

## Setup

1. **Install Claude Code CLI:**
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Install snap-happy globally:**
   ```bash
   npm install -g @mariozechner/snap-happy
   ```

3. **Link configurations via stow:**
   ```bash
   # From dotfiles root
   ./bin/manage_stow stow -p claude
   ```

4. **Verify MCP tools:**
   ```bash
   claude
   # In Claude CLI, type:
   /mcp
   ```

## MCP Tool Management

### Adding MCP Tools
```bash
# Add stdio MCP server
claude mcp add <name> "<command>"

# Add SSE MCP server  
claude mcp add --transport sse <name> <url>

# Add HTTP MCP server
claude mcp add --transport http <name> <url>
```

### Listing MCP Tools
```bash
claude mcp list
```

### Environment Variables
Set environment variables for MCP tools:
```bash
claude mcp add -e VAR=value <name> "<command>"
```

## Troubleshooting

### Docker MCP Issues
- Ensure Docker Desktop is running
- Verify container is accessible: `docker run --rm alpine/socat -V`
- Check network connectivity to `host.docker.internal:8811`

### Snap-happy Issues
- Grant screen recording permissions: System Preferences > Security & Privacy > Screen Recording
- Check Node.js installation: `node --version`
- Verify snap-happy installation: `npx @mariozechner/snap-happy --version`

### Permission Issues
- Check Claude settings in `.claude/settings.json`
- Ensure proper file permissions on configuration files

## Security Note

Use third-party MCP servers at your own risk due to potential prompt injection vulnerabilities. Only use trusted MCP tools from reliable sources.