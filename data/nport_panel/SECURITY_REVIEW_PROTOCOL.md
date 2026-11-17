# N-PORT security identity review ledger

## Purpose and scope

This is the durable human-review record for the N-PORT no-trade pilot. It is separate from the generated `security_crosswalk.csv`, which is rebuilt by the pipeline and must never be hand-edited.

The ledger contains one row per distinct `SECURITY_KEY` in the published crosswalk snapshot (rather than one row per fund-interval). A decision applies to that identifier only within the reviewed date scope. If a ticker, listing, share class, or corporate-action history changes over time, record the date range and use separate scoped rows rather than assuming a permanent ticker.

**No row is approved by default.** The initial status for every row is `NOT_REVIEWED`. Pipeline candidates, including N-PORT and OpenFIGI matches, are leads for review, not approvals.

## Review status vocabulary

- `NOT_REVIEWED`: not yet examined.
- `IN_REVIEW`: evidence being checked.
- `APPROVED`: identity and price-series match supported for the stated date scope.
- `REJECTED`: candidate is not the security/share class held.
- `UNRESOLVED`: evidence is insufficient or contradictory.
- `OUT_OF_SCOPE`: not a common-equity security that belongs in this return model.

Use `REVIEW_DECISION` to record the rationale and `REVIEW_NOTES` for supporting detail. Do not use `APPROVED` merely because two sources agree.

## Minimum evidence for approval

For every approval, establish and record:

1. The permanent identifier on the N-PORT holding (ISIN/CUSIP or other reliable issuer/security identifier).
2. The legal issuer and exact instrument: common stock, ADR/depositary receipt, preferred, REIT share, etc.; include share class where applicable.
3. The exchange/listing and trading currency represented by the selected price series.
4. That the candidate ticker and the selected historical adjusted-price series represent that exact instrument for the full interval.
5. Any ticker changes, mergers, delistings, splits, spin-offs, ADR ratio changes, or other corporate actions affecting the interval.
6. Evidence URLs and a concise explanation. Prefer issuer/exchange filings, SEC filings, official corporate-action notices, and authoritative security documentation. OpenFIGI and N-PORT are corroborating sources, not sole proof.

A U.S.-traded ADR is not automatically interchangeable with the ordinary foreign share. A ticker alias or OTC line is not automatically equivalent to a primary U.S. listing. Confirm currency and share-class continuity. If the instrument is foreign-listed, ADR-based, or has unresolved FX treatment, keep it unresolved until the return methodology explicitly supports it.

## How to use the fields

- Candidate fields and observed intervals are generated from the current crosswalk snapshot. Preserve them as source evidence; do not overwrite them with reviewer conclusions.
- `APPROVED_TICKER` is the exact price-series symbol to use only after approval.
- `APPROVED_SECURITY_IDENTIFIER_TYPE` and `APPROVED_SECURITY_IDENTIFIER_VALUE` record the reviewed identifier.
- `VALID_FROM` and `VALID_TO` define the period for which the decision applies (ISO YYYY-MM-DD).
- `EVIDENCE_URLS` accepts one or more URLs separated by ` | `.
- `REVIEWER` and `REVIEWED_AT_UTC` document provenance.
- If the same identifier needs different price symbols over time, split it into separate scoped review rows; do not silently replace one ticker globally.

## Review order

Start with rows marked `HIGH`, then `MEDIUM`, then `ROUTINE`. High priority includes identifier conflicts and invalid-price cases. Medium includes unmapped and missing-price cases. A row may have more than one review flag.

The current crosswalk snapshot contained 11 identifier-conflict records, 64 unmapped-ticker records, six missing endpoint-price records, and one invalid endpoint-price record. Those are interval-level records; this ledger deduplicates by security key, so row counts will differ.

## Promotion rule

The calculation pipeline must continue to treat all mappings as unreviewed until a later, separately tested change explicitly reads this ledger and enforces `REVIEW_STATUS == APPROVED`, the approved ticker, and the applicable date scope. This ledger alone does not change any existing calculation or retroactively validate the eight provisional intervals.

## Refreshing the queue

When the generated crosswalk changes, compare it with this ledger and add genuinely new security/date-scope rows. Do not regenerate and replace the whole ledger, because that would erase reviewer decisions. Retain old rows and decisions for audit history.
