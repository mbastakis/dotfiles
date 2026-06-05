# June PocketSmith Monthly Close Workflow

Before making any live PocketSmith calls, I would treat this as a two-phase job: first establish the exact identifiers and scope, then run a small number of targeted calls with pagination or date windows to avoid missing resources and truncated transaction output.

## Preflight

1. Confirm the close period: June 1 through June 30, including the relevant year and timezone.
2. Confirm the target business-plan note path and what section should be updated.
3. Inspect the existing business-plan note only after confirmation, to preserve its structure and avoid rewriting unrelated content.
4. Identify the required close outputs before calling PocketSmith, such as income, expenses, net cash flow, account balances, uncategorized transactions, unusual transactions, and business-plan implications.
5. Do not assume resource IDs from memory or prior runs.

## Resource Discovery To Avoid `That Resource Was Not Found`

1. Start with account and institution discovery calls, not transaction or category calls against guessed IDs.
2. Record the canonical IDs returned by PocketSmith for accounts, transaction accounts, categories, scenarios, and budgets as needed.
3. Use names only for human-readable matching; use returned IDs for all later calls.
4. If a resource lookup fails, stop and re-run discovery for that resource type instead of retrying variants of the same guessed ID.
5. Keep a short local working map during the session: resource name, resource type, canonical ID, and why it is needed.

## Transaction Retrieval Strategy To Avoid Truncation

1. Query transactions by explicit date range for June only.
2. Use pagination, limits, or smaller date windows rather than requesting the entire month if the result set may be large.
3. Prefer weekly windows if the API output is verbose or transaction count is unknown.
4. Request only fields needed for close analysis when the tool supports filtering or field selection.
5. If output is still too large, split by account first, then by week.
6. After each page or window, summarize counts and totals before moving on.
7. Track whether each account/date window is complete so no period is double-counted or skipped.

## Monthly Close Workflow

1. Discover accounts and confirm which accounts are in scope for the business close.
2. Retrieve June transactions for each in-scope account using paginated or weekly windows.
3. Check for uncategorized, duplicate-looking, pending, transfer, or anomalous transactions.
4. Retrieve category or budget metadata only after transactions show which categories matter.
5. Aggregate June totals by income, expense, transfers, category, account, and business-relevant groupings.
6. Compare June totals with the prior month or plan targets only if those figures are already available or can be fetched with similarly bounded calls.
7. Draft the close summary separately from the note edit.
8. Update only the relevant business-plan note section after the numbers are verified.
9. Preserve existing note structure, links, and frontmatter.
10. Report what changed, what assumptions were made, and what still needs human review.

## Delegation Points

I would delegate only when it reduces uncertainty or avoids broad, expensive exploration.

1. Delegate repository or vault reconnaissance if I need to locate the business-plan note and the location is not obvious from filenames or existing instructions.
2. Delegate web or external documentation research only if PocketSmith API behavior, pagination, or resource semantics are unclear from available tool descriptions.
3. Do not delegate live PocketSmith calls unless the delegate has the same explicit guardrails: no guessed IDs, bounded date ranges, pagination, and no note edits until the draft is verified.
4. Do not delegate note editing unless the target path and intended section are already known.

## Call-Efficiency Rules

1. Never call a transaction endpoint with a guessed account, category, or budget ID.
2. Never request all historical transactions for a monthly close.
3. Prefer one discovery call per resource type over multiple failed direct lookups.
4. Prefer bounded transaction calls by account and date window.
5. Summarize each retrieved batch immediately so large raw outputs do not need to be re-read.
6. Stop after the minimum data needed for the June close and business-plan update is collected.

## Failure Handling

1. If a resource is not found, re-discover the parent resource list and remap IDs.
2. If transaction output truncates, reduce the query scope by account, week, or page size.
3. If totals do not reconcile, inspect only the smallest suspicious slice rather than re-fetching everything.
4. If the business-plan note location or edit target is ambiguous, ask before editing.
5. If PocketSmith data is incomplete or unavailable, produce a draft close with explicit gaps instead of inventing figures.
