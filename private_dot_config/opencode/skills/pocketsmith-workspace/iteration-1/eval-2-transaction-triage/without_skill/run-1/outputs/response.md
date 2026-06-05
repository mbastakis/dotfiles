## PocketSmith May Cleanup Triage

I would update the transactions that have clear, low-risk meanings, and leave alone the ambiguous transfers/cash movements until they can be matched or confirmed.

### Update

| Transaction | Suggested treatment | Why |
|---|---|---|
| `PAYROLL MAY 2026` `+2223.35` | Categorize as salary/payroll income | Clear employer/payroll income. |
| `REMOTE WORKING MAY 2026` `+10.03` | Categorize as remote work allowance/reimbursement income | Clear work-related reimbursement/allowance. |
| `AKTSIALIS PHARMACY` `-5.52` | Categorize as pharmacy/health/medical expense | Merchant and amount are straightforward. |
| `ΑΓΟΡΑ 1948 5812` `-320` | Categorize as purchase/shopping only if this merchant is known | `ΑΓΟΡΑ` means purchase, but the merchant/category is not obvious. If there is no known rule, I would leave it uncategorized for review rather than guessing. |

### Leave Alone

| Transaction | Why |
|---|---|
| `Revolut9183` `-200` | Likely transfer/top-up/payment between accounts. Should not be categorized as spending unless the counterparty and purpose are known. |
| `ΑΝΑΛΗΨΗ ΕΞΩΤΕΡΙΚΟΥ` `-200` | Means foreign/overseas withdrawal. Cash withdrawals are usually better left uncategorized or treated specially until the actual cash spending is known. |
| `MICHAIL BASTAKIS` `+200` | Likely self-transfer or reimbursement from/to an own account. Needs matching/confirmation before categorizing as income. |

## Summary

Definite updates: `PAYROLL MAY 2026`, `REMOTE WORKING MAY 2026`, `AKTSIALIS PHARMACY`.

Conditional update: `ΑΓΟΡΑ 1948 5812`, only if prior knowledge identifies the merchant/category.

Leave alone: `Revolut9183`, `ΑΝΑΛΗΨΗ ΕΞΩΤΕΡΙΚΟΥ`, `MICHAIL BASTAKIS`.
