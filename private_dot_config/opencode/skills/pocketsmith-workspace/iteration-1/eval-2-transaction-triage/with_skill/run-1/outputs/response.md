## Transaction Triage

| Transaction | Decision | Proposed handling | Rationale |
| --- | --- | --- | --- |
| PAYROLL MAY 2026 +2223.35 | Update | Categorize as salary/payroll income. | Clear payroll label and positive income amount. |
| REMOTE WORKING MAY 2026 +10.03 | Update | Categorize as remote-work allowance, reimbursement, or employment-related income, depending on the existing category set. | Clear recurring work-related credit. |
| Revolut9183 -200 | Update only with the matching +200 transfer | Mark as transfer if it pairs with `MICHAIL BASTAKIS +200`; otherwise leave for review. | The amount exactly matches the apparent own-name inbound transfer, so this is likely an internal movement, but transfer semantics should be kept explicit. |
| AKTSIALIS PHARMACY -5.52 | Update | Categorize as pharmacy/health spending. | Merchant and amount are clear enough for a category match. |
| `ΑΓΟΡΑ 1948 5812` -320 | Leave alone | Keep uncategorized / needs review. | Opaque foreign-language POS-style label; not enough information to infer category safely. |
| `ΑΝΑΛΗΨΗ ΕΞΩΤΕΡΙΚΟΥ` -200 | Leave alone | Keep uncategorized / needs review. | This appears to be a foreign cash withdrawal, but cash use is ambiguous and should not be force-categorized without the user's rule. |
| `MICHAIL BASTAKIS` +200 | Update only with the matching Revolut transfer | Mark as transfer if it pairs with `Revolut9183 -200`; otherwise leave for review. | Own-name credit plus exact matching amount supports an internal transfer interpretation, but it should not be categorized as income. |

## Summary

I would update the clear payroll, remote-working credit, pharmacy purchase, and the `Revolut9183` / `MICHAIL BASTAKIS` pair only as a transfer pair. I would leave `ΑΓΟΡΑ 1948 5812` and `ΑΝΑΛΗΨΗ ΕΞΩΤΕΡΙΚΟΥ` unresolved.
