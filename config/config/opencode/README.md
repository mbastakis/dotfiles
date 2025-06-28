# OpenCode AI CLI Configuration

This directory contains the configuration for [OpenCode](https://opencode.ai), an AI coding agent for the terminal.

## Setup

1. **Install via dotfiles bootstrap:**
   ```bash
   # From dotfiles root - installs OpenCode and snap-happy via NPM globals
   ./bootstrap.sh --npm-globals
   ```

2. **Link configuration files:**
   ```bash
   # From dotfiles root - links OpenCode config via stow
   ./bin/manage_stow stow -p config
   ```

3. **Authenticate with Anthropic (Claude Pro/Max subscription):**
   ```bash
   opencode auth login
   # Select Anthropic from the provider list
   ```

4. **Set up OpenRouter API key (optional):**
   ```bash
   export OPENROUTER_API_KEY="your-openrouter-api-key"
   ```

5. **Ensure Docker is running for MCP tools:**
   - Docker Desktop should be running
   - MCP container should be accessible at `host.docker.internal:8811`

## Available Models

### Cloud Models (Authenticated)
- **Anthropic Claude Sonnet 4** (Default) - Via Claude Pro/Max subscription
- **OpenRouter Models** (via API key):
  - Claude 3.5 Sonnet
  - Claude 3.5 Haiku
  - GPT-4o
  - Gemini Pro 1.5

### Local Models (Ollama)
- **LLaVA Llama 3** - Vision-capable model
- **Qwen 2.5** - General purpose model
- **DeepSeek R1** - Reasoning-focused model
- **Llama 3.2** - Lightweight model

## Model Switching

Use the `/models` command within OpenCode to switch between available models:

```bash
opencode
# In OpenCode CLI:
/models
# Select from the list of available models
```

## MCP Tools

OpenCode is configured with the following Model Context Protocol tools:

### Docker MCP Tools
- **Connection**: TCP connection to Docker container at `host.docker.internal:8811`
- **Transport**: stdio via Alpine socat
- **Purpose**: Access to containerized MCP tools and services

### Snap-happy Screenshot Tool
- **Purpose**: Cross-platform screenshot capture for AI assistants
- **Functions**:
  - `GetLastScreenshot()` - Returns most recent screenshot as base64 PNG
  - `TakeScreenshot()` - Captures new screenshot
  - `ListWindows()` - Lists visible windows (macOS only)
- **Screenshot Path**: `~/Screenshots` (configurable via `SNAP_HAPPY_SCREENSHOT_PATH`)

## Configuration Structure

```json
{
  "$schema": "https://opencode.ai/config.json",
  "theme": "opencode",
  "model": "anthropic/claude-sonnet-4-20250514",
  "providers": {
    "openrouter": { ... },
    "ollama": { ... }
  },
  "mcp": {
    "localmcp": {
      "docker-mcp": { ... },
      "snap-happy": { ... }
    }
  }
}
```

## Environment Variables

- `OPENROUTER_API_KEY` - API key for OpenRouter models
- `SNAP_HAPPY_SCREENSHOT_PATH` - Custom screenshot directory (optional)

## Usage Tips

1. **First Run**: Authenticate with Anthropic before using cloud models
2. **Local Models**: Ensure Ollama is running (`ollama serve`) for local model access
3. **Docker MCP**: Verify Docker container is accessible before using MCP tools
4. **Screenshots**: Grant screen recording permissions on macOS for snap-happy
5. **Model Selection**: Use `/models` command to switch models during conversation

## Troubleshooting

- **Authentication Issues**: Run `opencode auth login` again
- **Local Models Not Available**: Check if Ollama is running with `ollama list`
- **MCP Tools Not Working**: Verify Docker container is running and accessible
- **Screenshot Permissions**: Check System Preferences > Security & Privacy > Screen Recording