---
name: linear-list
description: List and inspect Linear issues, teams, cycles, labels, and users using linear-cli.
version: 1.0.0
last_updated: 2026-02-22
---

# Linear List

## Overview

Use this skill when you need to fetch Linear data without changing state.

Prefer machine-readable responses for agent workflows:

```bash
--output json --compact
```

## Quick Start

```bash
# Verify auth
linear-cli whoami

# List your issues
linear-cli i list --mine --output json --compact

# Get one issue
linear-cli i get MBA-123 --output json --compact
```

## Issue Queries

```bash
# List by team
linear-cli i list -t Mbast --output json --compact

# List by status
linear-cli i list -t Mbast -s "In Progress" --output json --compact

# List your in-progress work
linear-cli i list --mine -s "In Progress" --output json --compact
```

## Context Queries

```bash
# Teams
linear-cli t list --output json --compact

# Current cycle for team
linear-cli c current -t Mbast --output json --compact

# Labels
linear-cli l list --output json --compact

# Users
linear-cli u list --output json --compact
```

## Output Guidance

- Return concise summaries (IDs, titles, status, assignee, priority)
- Include direct Linear URL when available in command output
- If no results, explicitly return an empty list and the filters used
