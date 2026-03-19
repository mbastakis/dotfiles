---
name: linear-projects
description: Manage Linear projects and project context (teams, cycles, labels, users) using linear-cli.
version: 1.0.0
last_updated: 2026-02-22
---

# Linear Projects

## Overview

Use this skill for project-level operations and planning context.

Prefer machine-readable output:

```bash
--output json --compact
```

## Project Commands

```bash
# List projects
linear-cli p list --output json --compact

# Get project details
linear-cli p get "<name>" --output json --compact

# Create project
linear-cli p create "<name>" --output json --compact

# List project members
linear-cli p members "<name>" --output json --compact
```

## Planning Context

```bash
# Teams
linear-cli t list --output json --compact

# Current cycle for a team
linear-cli c current -t Mbast --output json --compact

# Labels
linear-cli l list --output json --compact

# Users
linear-cli u list --output json --compact
```

## Output Guidance

- Return project ID/name/state/lead and URL when available
- For project creation, return the new project URL and next setup steps
- For context commands, summarize only fields relevant to the user request
