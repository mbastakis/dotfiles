# Analysis Workflow

**Goal**: Create an analysis ticket that evaluates options against criteria and produces a recommendation.

## When to Use

- Decision pending between known options
- "Compare X vs Y", "Evaluate Z", "Should we use A or B?"
- Need structured evaluation before choosing

## Workflow Steps

### Step 1: Identify Options

Ask: **"What options are you comparing?"**

If not provided, help identify:
- What are the candidates?
- Are there options they haven't considered?

### Step 2: Define Evaluation Criteria

Ask: **"What criteria matter most for this decision?"**

Common criteria:
- Performance, cost, complexity
- Team expertise, maintenance burden
- Scalability, security, ecosystem

### Step 3: Delegate for Context

| Need | Delegate To |
|------|-------------|
| Strategic trade-offs | `@oracle` |
| Codebase fit | `@explore` |
| External comparisons | `@web-researcher` |

### Step 4: Create Ticket

Use `linear_create_issue` with:
- **Title**: "Analysis: [decision topic]"
- **Description**: Use template below
- **Labels**: `analysis`
- **Team**: `{{TEAM}}`
- **Assignee**: `mbastakis`

### Step 5: Return Result

```
Created analysis ticket: "[title]"
Link: [linear_url]
Options to evaluate: [count]
Criteria defined: [count]
```

## Template

```markdown
## Objective

[What decision are we trying to make?]

## Options

| Option | Description |
|--------|-------------|
| Option A | Brief description |
| Option B | Brief description |
| Option C | Brief description |

## Evaluation Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Criterion 1 | High | Why it matters |
| Criterion 2 | Medium | Why it matters |
| Criterion 3 | Low | Why it matters |

## Analysis Matrix

| Criterion | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| Criterion 1 | | | |
| Criterion 2 | | | |
| Criterion 3 | | | |

## Acceptance Criteria

- [ ] All options evaluated against all criteria
- [ ] Pros and cons documented for each option
- [ ] Trade-offs clearly articulated
- [ ] Recommendation provided with rationale
- [ ] Risks identified for recommended option

## Recommendation

_To be filled after analysis_

### Rationale

_Why this option?_

### Risks & Mitigations

_What could go wrong and how to handle it_
```

## Checklist

Before creating the ticket, verify:

- [ ] All relevant options are identified
- [ ] Criteria are weighted by importance
- [ ] Criteria are measurable/comparable
- [ ] Acceptance criteria define "done"
- [ ] Decision-maker is clear
