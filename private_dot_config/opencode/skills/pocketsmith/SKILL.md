---
name: pocketsmith
description: Use this skill for PocketSmith MCP work: monthly finance closes, budget reviews, transaction categorization, feed-sync checks, runway/savings-rate reporting, and updates to finance notes from PocketSmith data. Trigger whenever the user mentions PocketSmith, monthly money review/close, uncategorized transactions, stale bank feeds, budget actuals, savings rate, runway, or asks to reconcile personal-finance data, even if they do not explicitly ask for a skill.
---

# PocketSmith

Use this workflow to avoid wasted PocketSmith calls, bad ID retries, context blowups, and premature note edits.

The main failure pattern is mixing discovery, data gathering, transaction cleanup, interpretation, and writing in one long context. Keep those phases separate. Use PocketSmith as the source of truth for numbers, but treat stale feeds and uncategorized transactions as first-class caveats.

## Core Workflow

### 1. Establish Scope Before Calling PocketSmith

Write a short working scope for yourself:

- Date range and period name, for example `2026-05-01` to `2026-05-31`.
- Desired output, for example monthly close, transaction cleanup, budget comparison, or note update.
- Whether mutations are allowed, especially `pocketsmith_update_transaction`.
- Any target note path or report destination.
- Known user rules, such as savings/investing allocation rules or category guardrails.

If the user asks for a note update, do not edit the note yet. First make the data state stable enough to summarize.

### 2. Resolve IDs Once

Use discovery calls before detail calls. Never guess IDs and never use placeholder IDs such as `0`.

Preferred first calls:

- `pocketsmith_get_current_user`
- `pocketsmith_list_transaction_accounts`
- `pocketsmith_get_data_feeds_connection_status`

Cache a compact ID map in your reasoning or response:

```text
PocketSmith ID map
- user_id: ...
- account: Bank name -> account_id ..., transaction_account_id ...
- feed status: Bank name -> status ..., last_successful_sync_at ...
```

PocketSmith commonly distinguishes account IDs from transaction account IDs. If a call returns `That resource was not found` or `That resource does not exist`, stop the retry loop and re-check the ID map. Do not try more than one nearby variation of the same failing call before returning to discovery.

### 3. Run Freshness Gate

Before interpreting a month as final, inspect feed status.

Treat these as blockers or caveats:

- `authorisation_failed`
- `provider_error`
- stale `last_successful_sync_at`
- missing expected payroll, rent, loan, or fixed bills
- obviously incomplete end-of-month account activity

If a key feed is stale:

- Mark the close as provisional.
- Avoid restating runway, savings rate, or cash position as final unless the stale feed is immaterial.
- Report what can still be trusted, such as already-imported categorized spending.
- Ask the user to sync/reauthorize if final metrics are required.

When the user says a feed was synced, rerun the feed status and all headline summaries before updating notes.

### 4. Pull Headline Summaries Before Transaction Detail

Use broad summary tools first so transaction work has context:

- `pocketsmith_month_end_review`
- `pocketsmith_get_budget_summary`
- `pocketsmith_spending_comparison`
- `pocketsmith_financial_health_snapshot` when cash/runway/net worth matters

Keep a compact metrics packet:

```text
Metrics packet
- income:
- expenses:
- net cashflow:
- savings rate:
- budget variance:
- refunds/credits:
- raw spending comparison:
- cash/runway:
- uncategorized count and amount:
- needs-review count:
```

Expect different tools to define expenses differently. For example, raw spending comparisons may include transfers, savings, investments, or uncategorized items that the budget summary excludes. Name the definition instead of forcing one number to explain everything.

### 5. Triage Transactions Narrowly

Use `pocketsmith_list_transactions` with the narrowest useful date range, account, category, and review filters. Prefer small, purposeful queries over broad dumps.

For each candidate update, build a table before mutating:

```text
| transaction_id | date | payee | amount | current state | proposed change | confidence | rationale |
```

Only update high-confidence items. Good candidates include clear payroll, known reimbursements, obvious subscriptions, clear card transfers, known merchant-category matches, and exact duplicate correction patterns already confirmed by the user.

Leave ambiguous items unresolved. Cash withdrawals, opaque POS labels, unknown person names, foreign-language merchant strings, and split transfers should stay uncategorized or be listed as caveats unless the user supplied the rule. A person-name transaction can be a transfer candidate only when it clearly matches the user's own name and the surrounding account movement supports that interpretation.

For transfer movements, be explicit about whether the update requires category change, `is_transfer: true`, or both.

### 6. Mutate Carefully

Before each `pocketsmith_update_transaction`, know:

- transaction ID
- current category/status when available
- new category or transfer flag
- reason the update is high confidence

After mutation, rerun the relevant summary tools and transaction counts. Do not use pre-update metrics in the final report.

If an update call fails, do not keep retrying blindly. Re-check whether the ID is a transaction ID, account ID, or transaction account ID, then make one corrected attempt.

### 7. Delegate Context-Heavy Work

Use the Task tool as a context firewall. Delegation is a safeguard, not a luxury.

Delegate when any of these happen:

- A PocketSmith output is truncated or saved to a large file.
- There are more than 5 ambiguous transactions to classify.
- You need to reconcile metrics across 3 or more PocketSmith tools.
- You need both finance interpretation and note editing.
- You have already had 2 PocketSmith resource/ID failures.

Good delegation packets:

```text
Ask a subagent to summarize this PocketSmith transaction output into:
- high-confidence category updates
- ambiguous items to leave alone
- totals by category/payee
- caveats that affect monthly close quality
Do not mutate PocketSmith.
```

Use `general` for finance-data digestion. Use `explore` only when the work is local file exploration or reading a saved tool-output file.

### 8. Write Notes Once The Data Is Stable

Do not update the user's finance note during discovery unless they explicitly ask for a provisional entry.

Before editing a note, confirm you have:

- feed freshness status
- final rerun headline metrics after any transaction updates
- unresolved transaction count and amount
- caveats for stale feeds, transfer semantics, refunds, and uncategorized items
- the exact note section to update

After editing a note, verify the change before final response:

- run `git diff -- <note-path>` when the note is in a git repo
- run `git status --short` to confirm only intended files changed
- if git is unavailable, read back the edited section and compare it to the intended metrics/caveats

Finance-note language should separate:

- clean facts from PocketSmith
- interpretation
- caveats
- decisions/actions

If the close is provisional, say so in the note. Do not bury data-quality issues behind confident metrics.

## Stop Rules

- After the first `That resource was not found`, re-resolve IDs instead of varying filters repeatedly.
- After the second ID/resource failure, stop analysis and produce a compact ID diagnosis.
- After one pass on ambiguous transaction semantics, record the caveat and move on.
- If feeds are stale and the user wants final runway or savings rate, pause and ask for sync/reauthorization instead of inventing a final answer.
- If the output is getting large, delegate before continuing.

## Report Format

For PocketSmith review work, use this structure unless the user asked for a specific note format:

```markdown
## PocketSmith Status
- Period:
- Feed freshness:
- Finality: clean / provisional / blocked

## Headline Metrics
- Income:
- Expenses:
- Net cashflow:
- Savings rate:
- Budget variance:
- Cash/runway, if reliable:

## Transaction Changes
| transaction_id | payee | amount | change | rationale |

## Unresolved Items
| payee | amount | reason left unresolved |

## Interpretation
- What the month means:
- What not to overread:

## Next Actions
- ...
```

For note updates, keep the chat summary brief and include the files changed plus remaining caveats.
