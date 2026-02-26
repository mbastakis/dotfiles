---
name: linear-create
description: Create Linear issues with consistent defaults and structured acceptance criteria using linear-cli.
version: 1.0.0
last_updated: 2026-02-22
---

# Linear Create

## Overview

Use this skill to create new Linear issues from scoped requests.

Default assumptions unless user says otherwise:

- Team: `Mbast`
- Assignee: `mbastakis`
- Priority: `3` (normal)

## Pre-Create Checks

```bash
# Verify auth
linear-cli whoami

# Quick duplicate scan
linear-cli i list -t Mbast --output json --compact
```

## Create Flow

```bash
# 1) Create issue
linear-cli i create "<title>" -t Mbast -p 3 --output json --compact

# 2) Assign owner
linear-cli i assign <ID> "mbastakis" --output json --compact

# 3) Set initial status/labels if needed
linear-cli i update <ID> -s "Todo" -l "enhancement" --output json --compact

# 4) Add structured body/details
linear-cli i comment <ID> -b "<markdown body>" --output json --compact
```

## Ticket Content Standard

Include:

- Summary (why this exists)
- Tasks checklist
- Acceptance criteria
- Technical notes / likely files

## Output Guidance

- Return issue ID, title, status, assignee, and URL
- Include created labels/priority/team in the final response
