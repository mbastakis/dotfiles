# Request Classification

**Purpose**: Classify incoming requests to route to the appropriate workflow.

## Classification Decision Tree

```
Request received
    │
    ├─► Contains "fix", "broken", "error", "bug", "crash"?
    │       └─► YES → Bug Fix Workflow
    │
    ├─► Contains "investigate", "research", "learn about", "explore how", "what is"?
    │       └─► YES → Research Workflow
    │
    ├─► Contains "analyze", "evaluate", "compare", "assess", "review", "audit"?
    │       └─► YES → Analysis Workflow
    │
    ├─► Contains "design", "architect", "plan system", "technical approach"?
    │       └─► YES → Architecture Workflow
    │
    ├─► Contains "build", "implement", "create", "add feature"?
    │       │
    │       ├─► Multiple components/stories needed (3+)?
    │       │       └─► YES → Epic Workflow
    │       │
    │       └─► Single, well-defined deliverable?
    │               └─► YES → Implementation Workflow
    │
    └─► Small, obvious, single-step (<30 min)?
            └─► YES → Quick Task Workflow
```

## Signal Words Matrix

| Workflow | Signal Words | Scope Indicators |
|----------|--------------|------------------|
| **Research** | investigate, explore, understand, learn about, what is, how does | Unknown territory, learning phase |
| **Analysis** | analyze, evaluate, compare, assess, review, audit | Known options, decision pending |
| **Architecture** | design, architect, plan, technical approach, system design | Technical decisions needed |
| **Epic** | build, implement, create, add feature | 3+ stories, multiple components |
| **Implementation** | build, implement, add, create | Single component, clear scope |
| **Bug Fix** | fix, broken, not working, error, crash, fails | Defect in existing functionality |
| **Quick Task** | update, change, rename, move, delete | <30 min work, obvious scope |

## Examples

### Research Workflow
- "I want to understand how BMAD structures their agents"
- "Investigate best practices for error handling in Go"
- "What authentication options exist for our API?"

### Analysis Workflow
- "Compare React vs Vue for our frontend rewrite"
- "Evaluate whether we should use Postgres or MongoDB"
- "Assess the security implications of adding OAuth"

### Architecture Workflow
- "Design the data model for our new feature"
- "Plan the technical approach for migrating to microservices"
- "Architect the caching layer for high-traffic endpoints"

### Epic Workflow
- "Build a user authentication system" (signup, login, password reset, 2FA)
- "Implement a dashboard with charts, filters, and export"
- "Create an admin panel for managing users and content"

### Implementation Workflow
- "Add a dark mode toggle to settings"
- "Implement the password reset email"
- "Create the user profile API endpoint"

### Bug Fix Workflow
- "The login button doesn't work on mobile"
- "Users are seeing a 500 error when uploading images"
- "Fix the date picker showing wrong timezone"

### Quick Task Workflow
- "Rename the 'utils' folder to 'helpers'"
- "Update the copyright year in the footer"
- "Change the default timeout from 30s to 60s"

## Ambiguity Resolution

When classification is unclear, ask ONE focused question:

| Ambiguity | Question to Ask |
|-----------|-----------------|
| Research vs Analysis | "Are you trying to **learn about** options, or **decide between** known options?" |
| Epic vs Implementation | "Will this require **multiple deployable pieces**, or is it **one focused change**?" |
| Architecture vs Implementation | "Do you need to **make design decisions** first, or is the approach **already decided**?" |
| Bug vs Feature | "Is this **fixing something broken**, or **adding something new**?" |

## Agent Delegation

Before creating tickets, gather context by delegating to specialized agents:

| Need | Delegate To | When |
|------|-------------|------|
| Find relevant code | `@explore` | Before any implementation ticket |
| Code/GitHub research | `@librarian` | Understanding libraries, finding examples |
| Web research | `@web-researcher` | Best practices, documentation, tutorials |

## Routing

After classification, load the appropriate workflow file:

| Classification | Load |
|----------------|------|
| Research | `workflows/manager/research/workflow.md` |
| Analysis | `workflows/manager/analysis/workflow.md` |
| Architecture | `workflows/manager/architecture/workflow.md` |
| Epic | `workflows/manager/epic/workflow.md` |
| Implementation | `workflows/manager/implementation/workflow.md` |
| Bug Fix | `workflows/manager/bug-fix/workflow.md` |
| Quick Task | `workflows/manager/quick-task/workflow.md` |
