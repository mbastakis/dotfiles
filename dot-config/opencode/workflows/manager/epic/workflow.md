# Epic Workflow

**Goal**: Create an epic (parent issue) with child stories that together deliver a complete feature.

## When to Use

- Feature requires 3+ user stories
- Multiple components or systems involved
- Work spans multiple deployments
- "Build X system", "Implement Y feature"

## Workflow Steps

### Step 1: Define Epic Scope

Ask: **"What is the user-facing outcome when this epic is complete?"**

Clarify:
- What's included in scope?
- What's explicitly excluded?
- What does success look like?

### Step 2: Delegate for Context

| Need | Delegate To |
|------|-------------|
| Existing code structure | `@explore` |

### Step 3: Break into Stories

Each story should be:
- **Independent**: Can be deployed on its own
- **Valuable**: Delivers user value
- **Estimable**: Small enough to estimate
- **Testable**: Has clear acceptance criteria

### Step 4: Identify Dependencies

Map story dependencies:
- Which stories block others?
- What's the critical path?
- Can any be parallelized?

### Step 5: Create Epic Issue

Use `linear_create_issue` with:
- **Title**: "[Feature Name]"
- **Description**: Use epic template below
- **Labels**: `epic`, `feature`
- **Team**: `{{TEAM}}`
- **Assignee**: `mbastakis`

### Step 6: Create Child Stories

For each story, use `linear_create_issue` with:
- **Title**: "[Story summary]"
- **Description**: Use story template
- **Parent**: Link to epic
- **Labels**: `story`

### Step 7: Set Up Dependencies

Use `linear_update_issue` to set `blockedBy` relationships.

### Step 8: Return Result

```
Created epic: "[title]"
Epic link: [linear_url]

Stories created:
1. [MBA-XX] [Story 1 title] - [link]
2. [MBA-XX] [Story 2 title] - [link] (blocked by #1)
3. [MBA-XX] [Story 3 title] - [link] (blocked by #1)

Dependency graph:
Story 1 → Story 2
       → Story 3
```

## Epic Template

```markdown
## Overview

[What are we building and why? What user problem does this solve?]

## Scope

### In Scope
- Item 1
- Item 2

### Out of Scope
- Item 1
- Item 2

## User Stories

| # | Story | Status |
|---|-------|--------|
| 1 | [Story 1 title] | 🔲 Not Started |
| 2 | [Story 2 title] | 🔲 Not Started |
| 3 | [Story 3 title] | 🔲 Not Started |

## Dependencies

```
Story 1 (foundation)
    ├── Story 2 (depends on 1)
    └── Story 3 (depends on 1)
```

## Acceptance Criteria

- [ ] All stories completed
- [ ] Integration tested end-to-end
- [ ] Documentation updated
- [ ] No regressions in existing functionality

## Technical Notes

[Any technical context for implementers]
```

## Story Template

```markdown
## User Story

As a [user type], I want to [action] so that [benefit].

## Context

[Link to parent epic, relevant architecture decisions]

## Tasks

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Acceptance Criteria

- [ ] Given [context], when [action], then [result]
- [ ] Given [context], when [action], then [result]

## Technical Notes

[Implementation hints, relevant files, patterns to follow]

## Files Likely Affected

- `path/to/file1.ts`
- `path/to/file2.ts`
```

## Checklist

Before creating the epic, verify:

- [ ] Epic scope is clear (in/out of scope defined)
- [ ] Stories are independent and valuable
- [ ] Each story has acceptance criteria
- [ ] Dependencies are mapped
- [ ] No story is too large (>3 days = split it)
