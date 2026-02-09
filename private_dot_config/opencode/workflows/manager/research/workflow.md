# Research Workflow

**Goal**: Create a research ticket that produces documented findings with evidence and recommendations.

## When to Use

- Unknown territory that needs exploration
- "What is X?", "How does Y work?", "What options exist for Z?"
- Learning phase before making decisions

## Workflow Steps

### Step 1: Clarify Research Scope

Ask: **"What specific questions do you need answered?"**

Determine research type:
- **Market research** → external data, competitors, trends
- **Technical research** → libraries, patterns, approaches
- **Domain research** → regulations, industry standards

### Step 2: Delegate for Context

| Research Type | Delegate To |
|---------------|-------------|
| Technical (libraries, code) | `@librarian` |
| Best practices, docs | `@web-researcher` |
| Codebase patterns | `@explore` |

### Step 3: Create Ticket

Use `linear_create_issue` with:
- **Title**: "Research: [topic]"
- **Description**: Use template below
- **Labels**: `research`
- **Team**: `{{TEAM}}`
- **Assignee**: `mbastakis`

### Step 4: Return Result

```
Created research ticket: "[title]"
Link: [linear_url]
Questions to answer: [count]
Research type: [market/technical/domain]
```

## Template

```markdown
## Objective

[What question are we trying to answer?]

## Research Type

[Market / Technical / Domain]

## Questions to Answer

- [ ] Question 1
- [ ] Question 2
- [ ] Question 3

## Sources to Consult

- [ ] Source 1
- [ ] Source 2

## Acceptance Criteria

- [ ] All questions answered with evidence
- [ ] Sources cited for key findings
- [ ] Findings documented in summary
- [ ] Recommendations provided (if applicable)

## Findings

_To be filled during research_

## Recommendations

_To be filled after research_
```

## Checklist

Before creating the ticket, verify:

- [ ] Research objective is clear and specific
- [ ] Questions are answerable (not too broad)
- [ ] Research type is identified
- [ ] Relevant sources are suggested
- [ ] Acceptance criteria define "done"
