# June PocketSmith Monthly Close Workflow

This is the exact workflow I would follow before making any live PocketSmith calls. I would not edit the business-plan note until the PocketSmith data state is stable and the final metrics have been rerun.

## 1. Establish Scope Before Live Calls

- Period: `2026-06-01` through `2026-06-30`, unless the user confirms a different June year.
- Output: June monthly close plus an update to the business-plan note.
- Mutations: I would assume no PocketSmith mutations are allowed unless the user explicitly approves transaction updates.
- Note edits: I would defer all note edits until after feed freshness, headline metrics, unresolved items, and caveats are known.
- Quality goal: avoid guessed IDs, repeated failed calls, broad transaction dumps, and context blowups from large transaction output.

If the year or target business-plan note path is not already known from context, I would ask one short clarification before making calls.

## 2. Resolve IDs Once, Then Cache Them

First PocketSmith calls would be discovery only:

1. `pocketsmith_get_current_user`
2. `pocketsmith_list_transaction_accounts`
3. `pocketsmith_get_data_feeds_connection_status`

I would build and keep a compact ID map before calling any detail endpoint:

```text
PocketSmith ID map
- user_id: ...
- account: Bank/account name -> account_id ..., transaction_account_id ...
- feed status: Bank/account name -> status ..., last_successful_sync_at ...
```

Rules for avoiding `That resource was not found`:

- Never guess IDs.
- Never use placeholder IDs such as `0`.
- Treat account IDs and transaction account IDs as different values unless the tool documentation/output proves otherwise.
- After the first `That resource was not found`, stop retrying variants and return to the ID map.
- After the second resource/ID failure, stop live analysis and produce a compact ID diagnosis instead of burning more calls.

## 3. Run Feed Freshness Gate

Before interpreting June as final, I would inspect feed status from `pocketsmith_get_data_feeds_connection_status`.

The close becomes provisional or blocked if any key feed shows:

- `authorisation_failed`
- `provider_error`
- stale `last_successful_sync_at`
- missing expected payroll, rent, loan, tax, subscription, or other fixed business/personal flows
- obviously incomplete end-of-month activity

If a key feed is stale, I would not state final runway, savings rate, cash position, or business-plan implications. I would report what is still reliable and ask the user to sync or reauthorize before finalizing.

## 4. Pull Headline Summaries Before Transaction Detail

Only after IDs and feed freshness are stable would I call broad summary tools:

1. `pocketsmith_month_end_review` for June close metrics and review flags.
2. `pocketsmith_get_budget_summary` for actuals vs budget.
3. `pocketsmith_spending_comparison` for month-over-month spending context.
4. `pocketsmith_financial_health_snapshot` only if the business-plan update needs cash, runway, net worth, debt, or savings-rate implications.

I would store a compact metrics packet:

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

I would not force all tools to reconcile to one expense number. If definitions differ, I would label them clearly, for example budgeted expenses vs raw spending including transfers, savings, investments, or uncategorized items.

## 5. Triage Transactions Narrowly

I would call `pocketsmith_list_transactions` only after summaries show exactly what needs investigation.

Query strategy:

- Use the June date range only.
- Add account filters only from the resolved ID map.
- Add category, uncategorized, or needs-review filters where possible.
- Prefer several narrow queries over one broad month dump.
- Avoid retrieving full transaction history unless a specific reconciliation problem requires it.

Before any mutation, I would prepare this table:

```markdown
| transaction_id | date | payee | amount | current state | proposed change | confidence | rationale |
|---|---|---:|---:|---|---|---|---|
```

I would only propose high-confidence updates, such as clear payroll, known reimbursements, obvious subscriptions, known merchant/category matches, or transfer patterns already confirmed by the user.

Ambiguous cash withdrawals, opaque POS labels, unknown person names, foreign-language merchant strings, and split transfers would stay unresolved with caveats unless the user has supplied a rule.

## 6. Avoid Truncated Transaction Output

To avoid the prior truncation problem:

- I would not request a broad June transaction dump at the start.
- I would narrow by review status, category, account, or date segment before listing transactions.
- If the tool output is still large or saved externally, I would stop and delegate summarization before continuing.
- I would ask the delegate to extract only decision-relevant fields: transaction IDs, dates, payees, amounts, categories, proposed actions, totals, and caveats.
- I would not continue interpreting a truncated transaction list as complete.

## 7. Delegation Points

I would delegate as a context firewall, not as a last resort.

I would delegate to `general` when:

- A PocketSmith transaction output is truncated or saved to a large file.
- There are more than 5 ambiguous transactions to classify.
- I need to reconcile metrics across 3 or more PocketSmith summary tools.
- The monthly close requires both finance interpretation and note-writing synthesis.
- I have already hit 2 PocketSmith resource/ID failures.

Example delegation packet for transaction digestion:

```text
Summarize this PocketSmith transaction output for the June close.
Return:
- high-confidence category or transfer updates
- ambiguous items to leave unresolved
- totals by category/payee
- caveats affecting close quality
Do not mutate PocketSmith.
```

I would delegate to `explore` only for local file work, such as locating and reading the business-plan note or reading a saved large PocketSmith output file. I would not use `explore` for live PocketSmith calls.

## 8. Mutation Policy

For this requested workflow, I would not mutate PocketSmith without explicit approval.

If the user later approves transaction cleanup, then before each `pocketsmith_update_transaction` I would require:

- transaction ID
- current category/status
- new category and/or `is_transfer` change
- high-confidence rationale

After any mutation, I would rerun relevant headline summaries and transaction counts. I would never use pre-update metrics in the final monthly close or note update.

## 9. Business-Plan Note Update Sequence

I would edit the business-plan note only after data is stable.

Before editing, I would confirm:

- feed freshness status
- final rerun headline metrics after any approved transaction updates
- unresolved transaction count and amount
- caveats for stale feeds, transfer semantics, refunds, and uncategorized items
- exact note path and section to update

The note update would separate:

- clean facts from PocketSmith
- interpretation for the business plan
- caveats and provisionality
- decisions or next actions

If June is provisional, the note would say so explicitly.

## 10. Final Report Format

After live work is complete, I would report in this structure:

```markdown
## PocketSmith Status
- Period: June 2026
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
|---|---:|---:|---|---|

## Unresolved Items
| payee | amount | reason left unresolved |
|---|---:|---|

## Business-Plan Note Update
- File changed:
- Section changed:
- Main interpretation added:
- Caveats preserved:

## Next Actions
- ...
```

## Stop Rules

- First `That resource was not found`: re-check the ID map instead of retrying variants.
- Second resource/ID failure: stop and produce an ID diagnosis.
- Truncated transaction output: delegate summarization before interpreting it.
- Stale key feed: mark the close provisional or blocked and ask for sync/reauthorization if final metrics are required.
- Ambiguous transaction semantics after one pass: record the caveat and move on.
- Note editing requested while data is unstable: defer the edit unless the user explicitly wants a provisional entry.
