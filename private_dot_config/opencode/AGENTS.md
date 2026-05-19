# OpenCode Agents

Agent delegation guidance.

## Delegation Triggers

| Pattern                                          | Delegate to    |
| ------------------------------------------------ | -------------- |
| External package internals, upstream source evidence, issues/PR history | librarian |
| Web docs, tutorials, best practices, comparisons | web-researcher |
| User explicitly invokes `@scout` for broad repo/reference reconnaissance | scout |
| Crawl/persist web content, `/crawl` command      | crawl          |
| 2+ modules/directories involved                  | explore        |
| "Where is X?" questions                          | explore        |

## Cross-Cutting Rules

- Librarian can delegate to web-researcher for URL discovery before investigating with `gh` CLI.
- Scout is manual-only; do not auto-delegate to scout unless the user explicitly asks for `@scout`.
