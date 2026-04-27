# OpenCode Agents

Agent delegation guidance.

## Delegation Triggers

| Pattern                                          | Delegate to    |
| ------------------------------------------------ | -------------- |
| External library / "how does [package] work?"    | librarian      |
| Web docs, tutorials, best practices, comparisons | web-researcher |
| Crawl/persist web content, `/crawl` command      | crawl          |
| 2+ modules/directories involved                  | explore        |
| "Where is X?" questions                          | explore        |

## Cross-Cutting Rules

- Librarian can delegate to web-researcher for URL discovery before investigating with `gh` CLI.
