---
name: linear-workflow
description: Run day-to-day issue workflow actions (start, stop, close, assign, comment) using linear-cli.
version: 1.0.0
last_updated: 2026-02-22
---

# Linear Workflow

## Overview

Use this skill for routine issue state transitions.

## Action Commands

```bash
# Start work (moves to In Progress + assigns)
linear-cli i start <ID> --output json --compact

# Stop / pause work (move back to Todo)
linear-cli i update <ID> -s "Todo" --output json --compact

# Close work (done/completed)
linear-cli i close <ID> --output json --compact

# Assign issue
linear-cli i assign <ID> "<user>" --output json --compact

# Add handoff or status comment
linear-cli i comment <ID> -b "<handoff/status note>" --output json --compact
```

## Recommended Flow

```bash
# Start
linear-cli i start <ID> --output json --compact

# Record progress
linear-cli i comment <ID> -b "Started implementation; plan is ..." --output json --compact

# Close
linear-cli i close <ID> --output json --compact
```

## Output Guidance

- Report transition and actor (e.g., Todo -> In Progress)
- Include issue ID/title/URL after each state-changing action
- Include comment summary for handoffs and closures
