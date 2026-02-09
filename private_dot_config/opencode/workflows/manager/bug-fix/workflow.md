# Bug Fix Workflow

**Goal**: Create a bug ticket with reproduction steps, expected behavior, and fix criteria.

## When to Use

- Something is broken that used to work
- "Fix X", "Y is not working", "Error when Z"
- Defect in existing functionality

## Workflow Steps

### Step 1: Clarify the Bug

Ask if not provided:
- **"What are the exact steps to reproduce this?"**
- **"What should happen vs what actually happens?"**

### Step 2: Gather Codebase Context

Delegate to `@explore`:
- Find the affected code
- Identify related files
- Locate relevant tests

### Step 3: Assess Severity

| Severity | Criteria |
|----------|----------|
| Critical | System unusable, data loss, security issue |
| High | Major feature broken, no workaround |
| Medium | Feature impaired, workaround exists |
| Low | Minor issue, cosmetic, edge case |

### Step 4: Create Ticket

Use `linear_create_issue` with:
- **Title**: "Fix: [brief description of bug]"
- **Description**: Use template below
- **Labels**: `bug`, + severity label
- **Priority**: Based on severity
- **Team**: `{{TEAM}}`
- **Assignee**: `mbastakis`

### Step 5: Return Result

```
Created bug ticket: "[title]"
Link: [linear_url]
Severity: [level]
Affected files: [list]
```

## Template

```markdown
## Bug Description

[Clear, one-sentence description of what's broken]

## Severity

[Critical / High / Medium / Low] - [brief justification]

## Environment

- Browser/Platform: [if relevant]
- Version: [if relevant]
- User type: [if relevant]

## Reproduction Steps

1. Step 1
2. Step 2
3. Step 3
4. Observe the bug

## Expected Behavior

[What should happen]

## Actual Behavior

[What actually happens]

## Screenshots/Logs

[If available]

## Acceptance Criteria

- [ ] Bug can be reproduced
- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Fix verified in [environment]
- [ ] Regression test added
- [ ] No new bugs introduced

## Technical Notes

[Any initial investigation findings]

## Files Likely Affected

- `path/to/file1.ts` - [suspected issue]

## Related

- Related issues: [if any]
- When introduced: [if known]
```

## Checklist

Before creating the ticket, verify:

- [ ] Reproduction steps are specific and repeatable
- [ ] Expected vs actual behavior is clear
- [ ] Severity is assessed
- [ ] Codebase context gathered via `@explore`
- [ ] Regression test requirement included
