# Implementation Workflow

**Goal**: Create a single implementation ticket (story) with clear tasks and acceptance criteria.

## When to Use

- Single, well-defined piece of work
- Clear scope, one component
- "Add X feature", "Implement Y endpoint"
- Can be completed in 1-3 days

## Workflow Steps

### Step 1: Clarify Scope

Ask if unclear: **"What exactly should this do when complete?"**

Ensure:
- Single deliverable outcome
- Clear boundaries
- Testable result

### Step 2: Gather Codebase Context

**ALWAYS** delegate to `@explore`:
- Find relevant files
- Identify patterns to follow
- Locate similar implementations

### Step 3: Define Acceptance Criteria

Use Given/When/Then format:
- Given [context/precondition]
- When [action is taken]
- Then [expected result]

### Step 4: List Technical Tasks

Break into implementation steps:
- Each task = one logical unit of work
- Order by dependency
- Include test tasks

### Step 5: Create Ticket

Use `linear_create_issue` with:
- **Title**: "[Action] [target]" (e.g., "Add dark mode toggle to settings")
- **Description**: Use template below
- **Labels**: `enhancement` or appropriate label
- **Team**: `{{TEAM}}`
- **Assignee**: `mbastakis`

### Step 6: Return Result

```
Created implementation ticket: "[title]"
Link: [linear_url]
Tasks: [count]
Files affected: [list]
```

## Template

```markdown
## Summary

[One sentence: what are we building and why?]

## User Story

As a [user type], I want to [action] so that [benefit].

## Tasks

- [ ] Task 1: [specific action]
- [ ] Task 2: [specific action]
- [ ] Task 3: Write tests
- [ ] Task 4: Update documentation (if needed)

## Acceptance Criteria

- [ ] Given [context], when [action], then [result]
- [ ] Given [context], when [action], then [result]
- [ ] Given [edge case], when [action], then [handles gracefully]

## Technical Notes

[Implementation hints, patterns to follow, decisions already made]

## Files Likely Affected

- `path/to/file1.ts` - [what changes]
- `path/to/file2.ts` - [what changes]

## Related

- Related issue: [link if any]
- Architecture decision: [link if any]
```

## Checklist

Before creating the ticket, verify:

- [ ] Scope is single, clear deliverable
- [ ] Codebase context gathered via `@explore`
- [ ] Acceptance criteria are testable
- [ ] Tasks are ordered by dependency
- [ ] Files affected are identified
- [ ] No blockers or dependencies exist (or they're documented)
