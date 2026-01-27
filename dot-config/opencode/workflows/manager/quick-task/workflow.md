# Quick Task Workflow

**Goal**: Create a minimal ticket for small, obvious work that needs tracking but not ceremony.

## When to Use

- Work is <30 minutes
- Scope is completely obvious
- Single file or trivial change
- "Rename X", "Update Y", "Change Z to W"

## Workflow Steps

### Step 1: Verify It's Actually Quick

If any of these are true, use a different workflow:
- Requires investigation → Research Workflow
- Has multiple parts → Implementation Workflow
- Touches critical path → Implementation Workflow (more ceremony)

### Step 2: Create Minimal Ticket

Use `linear_create_issue` with:
- **Title**: "[Action] [target]" (e.g., "Update copyright year in footer")
- **Description**: Use template below (keep it short!)
- **Labels**: `chore` or appropriate label
- **Team**: `{{TEAM}}`
- **Assignee**: `mbastakis`

### Step 3: Return Result

```
Created quick task: "[title]"
Link: [linear_url]
```

## Template

```markdown
## Task

[One sentence: what to do]

## Location

[File or area affected]

## Done When

- [ ] [Single, clear completion criterion]
```

## Examples

### Rename a Folder
```markdown
## Task

Rename `utils/` folder to `helpers/`

## Location

`src/utils/` → `src/helpers/`

## Done When

- [ ] Folder renamed and all imports updated
```

### Update a Constant
```markdown
## Task

Change default timeout from 30s to 60s

## Location

`src/config/constants.ts`

## Done When

- [ ] DEFAULT_TIMEOUT changed to 60000
```

### Fix a Typo
```markdown
## Task

Fix typo "recieve" → "receive" in error message

## Location

`src/errors/messages.ts`

## Done When

- [ ] Typo corrected
```

## Checklist

Before creating the ticket, verify:

- [ ] Task is truly quick (<30 min)
- [ ] Scope is obvious (no ambiguity)
- [ ] Single completion criterion is enough
- [ ] Not touching critical functionality
