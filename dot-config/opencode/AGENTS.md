# OpenCode Configuration

Custom commands, agents, and skills for OpenCode AI assistant.

## Structure

| Path                  | Purpose                              |
| --------------------- | ------------------------------------ |
| `opencode.jsonc`      | Main config (provider, MCP, permissions) |
| `command/*.md`        | Custom slash commands                |
| `agent/*.md`          | Custom subagents                     |
| `skill/*/SKILL.md`    | Skills with scripts and references   |

## Commands

| Command         | Purpose                    |
| --------------- | -------------------------- |
| `opencode`      | Start OpenCode             |
| `oc`            | Alias for opencode         |
| `bun install`   | Install dependencies       |

## Custom Commands

Create `command/<name>.md` with YAML frontmatter:

```markdown
---
description: Brief description shown in command list
model: provider/model-id
---

# Command Title

Instructions for the command in markdown...
```

**Current commands**:
- `research_codebase.md` — Document codebase through parallel research
- `create_plan.md` — Create detailed implementation plans

## Custom Agents

Create `agent/<name>.md` with YAML frontmatter:

```markdown
---
mode: subagent
tools:
  - read
  - write
  - bash
  - skill
---

# Agent Name

Agent instructions in markdown...
```

**Current agents**:
- `web-researcher.md` — Web crawling via crawl4ai skill

## Skills

Skills live in `skill/<name>/` with this structure:
```
skill/<name>/
├── SKILL.md          # Instructions and documentation
├── scripts/          # Executable scripts
├── references/       # Reference documentation
└── tests/            # Test files
```

### crawl4ai Skill

| Script                  | Purpose                      |
| ----------------------- | ---------------------------- |
| `basic_crawler.py`      | Single URL crawling          |
| `site_crawler.py`       | Multi-page site crawling     |
| `batch_crawler.py`      | Batch URL processing         |
| `extraction_pipeline.py`| Structured data extraction   |

Run with: `uvx --from crawl4ai python scripts/<script>.py`

## Gotchas

- Commands use YAML frontmatter — `---` delimiters required
- Model IDs must match provider format exactly (e.g., `amazon-bedrock/anthropic.claude-opus-4-20250514-v1:0`)
- Skills loaded via the `skill` tool — agents need `skill` in tools list
- `node_modules/` is gitignored — run `bun install` after clone
