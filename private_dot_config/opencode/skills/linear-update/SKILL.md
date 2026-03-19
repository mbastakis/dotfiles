---
name: linear-update
description: Update existing Linear issues (status, labels, assignment, comments) using linear-cli.
version: 1.0.0
last_updated: 2026-02-22
---

# Linear Update

## Overview

Use this skill for non-creation issue changes: status, labels, assignee, and notes.

## Safe Update Sequence

```bash
# 1) Inspect current state first
linear-cli i get <ID> --output json --compact

# 2) Apply requested update
linear-cli i update <ID> -s "In Progress" -l "backend,work" --output json --compact

# 3) Re-fetch to verify
linear-cli i get <ID> --output json --compact
```

## Common Operations

```bash
# Status only
linear-cli i update <ID> -s "Todo" --output json --compact

# Labels only
linear-cli i update <ID> -l "bug,urgent" --output json --compact

# Reassign
linear-cli i assign <ID> "mbastakis" --output json --compact

# Add context
linear-cli i comment <ID> -b "<update note>" --output json --compact
```

## Output Guidance

- Report exactly what changed (before -> after)
- Include issue URL and final status/assignee/labels
- If no change was needed, say so explicitly
