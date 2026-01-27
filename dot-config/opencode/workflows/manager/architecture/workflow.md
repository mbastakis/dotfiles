# Architecture Workflow

**Goal**: Create an architecture ticket that documents technical decisions with ADRs (Architecture Decision Records).

## When to Use

- Technical decisions need to be made before implementation
- "Design the system for X", "Plan the technical approach"
- New component, integration, or significant change

## Workflow Steps

### Step 1: Understand Context

Ask: **"What problem are we solving and what constraints exist?"**

Gather:
- Business requirements driving the architecture
- Performance/scale requirements
- Team expertise and timeline constraints
- Existing system context

### Step 2: Delegate for Context

| Need | Delegate To |
|------|-------------|
| Existing patterns | `@explore` |
| Design review | `@oracle` |
| External patterns | `@web-researcher` |

### Step 3: Identify Decisions

List the architectural decisions needed:
- Technology choices
- Pattern selection
- Integration approaches
- Data model design

### Step 4: Create Ticket

Use `linear_create_issue` with:
- **Title**: "Architecture: [component/system]"
- **Description**: Use template below
- **Labels**: `architecture`
- **Team**: `{{TEAM}}`
- **Assignee**: `mbastakis`

### Step 5: Return Result

```
Created architecture ticket: "[title]"
Link: [linear_url]
Decisions to make: [count]
ADRs to document: [list]
```

## Template

```markdown
## Context

[Why is this architecture needed? What problem are we solving?]

## Requirements

### Functional
- [ ] Requirement 1
- [ ] Requirement 2

### Non-Functional
- [ ] Performance: [target]
- [ ] Scalability: [target]
- [ ] Security: [requirements]

## Constraints

- Constraint 1 (e.g., must integrate with X)
- Constraint 2 (e.g., team knows Y)
- Constraint 3 (e.g., budget limit)

## Decisions to Make

- [ ] Decision 1: [question]
- [ ] Decision 2: [question]
- [ ] Decision 3: [question]

## Acceptance Criteria

- [ ] All decisions documented as ADRs
- [ ] Trade-offs clearly articulated
- [ ] Diagrams created (if applicable)
- [ ] Implementation path is clear
- [ ] Risks identified and mitigated

---

## ADR 1: [Decision Title]

### Status
Proposed / Accepted / Deprecated / Superseded

### Context
[Why is this decision needed?]

### Options Considered
1. **Option A**: Description
   - Pros: ...
   - Cons: ...
2. **Option B**: Description
   - Pros: ...
   - Cons: ...

### Decision
[What was decided and why]

### Consequences
- Positive: ...
- Negative: ...
- Risks: ...

---

## ADR 2: [Decision Title]

_Use same format as ADR 1_

---

## Diagrams

_Add system diagrams, data flow diagrams, etc._

## Implementation Notes

_Key implementation considerations for developers_
```

## Checklist

Before creating the ticket, verify:

- [ ] Context explains the "why"
- [ ] Requirements are specific and measurable
- [ ] Constraints are documented
- [ ] All key decisions are listed
- [ ] ADR template is ready for each decision
- [ ] Acceptance criteria define "done"
