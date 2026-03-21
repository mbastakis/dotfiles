# OpenCode OMO Profile

Isolated OpenCode configuration root reserved for `oh-my-openagent` experiments.

## Purpose

- Deploys to `~/.config/opencode-omo/`
- Kept separate from the primary profile at `~/.config/opencode/`
- Launched through the `omo` shell alias, which overrides `OPENCODE_CONFIG` and `OPENCODE_CONFIG_DIR` for that process

## Files

| Path | Purpose |
| --- | --- |
| `opencode.jsonc` | Isolated OpenCode config with `oh-my-opencode` plugin enabled |
| `oh-my-opencode.json` | OMO agent/category model profile |
| `tui.json` | TUI theme for the isolated profile |
| `dot_gitignore` | Target `.gitignore` for local install artifacts |

The directory is intentionally minimal so OMO-specific installer output and plugin state stay outside the primary OpenCode profile.

## Current Install Baseline

- Installed from the OMO installation guide using `bunx oh-my-opencode install --no-tui`
- Current checked-in profile reflects `--openai=yes` with the rest of the installer flags left disabled
- Bedrock is not represented by a dedicated OMO installer flag, so the checked-in baseline keeps the installer-generated OpenAI profile without additional Bedrock-specific overrides

## Explicit Model Map

- `oh-my-opencode.json` is hand-pinned to the published OMO agent/category model guidance rather than the installer's generic fallback output
- Claude-oriented agents use `opencode/claude-*` models because local OpenCode currently exposes OpenCode Zen, OpenAI, and Google providers directly
- GPT-oriented agents use `openai/gpt-5.4` and `openai/gpt-5.3-codex`
- Utility and category models use the documented fast/default families available locally: `opencode/minimax-m2.5`, `google/gemini-3.1-pro`, and `opencode/kimi-k2.5`
