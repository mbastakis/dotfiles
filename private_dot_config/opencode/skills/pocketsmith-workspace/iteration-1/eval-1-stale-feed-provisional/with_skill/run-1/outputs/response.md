## PocketSmith Status
- Period: May finance review, presumed `2026-05-01` to `2026-05-31` unless the user specifies a different May.
- Feed freshness: Not clean. NBG is `authorisation_failed`; Eurobank is stale since March.
- Finality: provisional / blocked for final close.

## Headline Metrics
- Income: Report PocketSmith's current May income as `EUR 0`, but treat it as a data-quality signal, not a reliable conclusion.
- Expenses: Report only already-imported May expenses that are present in PocketSmith, with a caveat that missing NBG/Eurobank activity may materially change the total.
- Net cashflow: Do not treat as final because income and bank activity may be incomplete.
- Savings rate: Refuse to state as final while key feeds are failed or stale and May income appears missing.
- Budget variance: May be discussed only as provisional against imported/categorized transactions.
- Cash/runway: Refuse to state as final unless the stale/failed feeds are proven immaterial.

## Transaction Changes
No transaction changes should be made for this eval. Do not call live PocketSmith tools and do not modify PocketSmith.

## Unresolved Items
| item | reason left unresolved |
| --- | --- |
| NBG feed | `authorisation_failed`; May activity may be missing or incomplete. |
| Eurobank feed | Stale since March; May activity is not reliable for final review. |
| May income showing `EUR 0` | Likely incomplete or missing payroll/import data; cannot be interpreted as true zero income without refreshed feeds and transaction verification. |

## Interpretation
- What can be reported: a provisional May finance review based on the data currently present in PocketSmith, clearly labeled as incomplete.
- What the month may indicate: imported spending patterns, visible budget pressure, and any already-present categorized transactions can be summarized as directional findings.
- What not to overread: `EUR 0` income, net cashflow, savings rate, runway, final cash position, and final budget performance should not be treated as final because core feeds are failed/stale.
- Data-quality caveat: the failed NBG authorization and Eurobank staleness are not minor footnotes; they are blockers for a final monthly close if those accounts carry payroll, bills, transfers, savings, or ordinary spending.

## Next Actions
- Reauthorize or fix the NBG connection.
- Refresh or reconnect Eurobank.
- After feeds sync successfully, rerun feed status and all headline summaries before producing a final May close.
- Verify expected payroll/income transactions before accepting or explaining `EUR 0` income.
