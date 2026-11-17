# AB / IVV return-coverage pilot inputs

These compact CSV inputs were extracted from the uploaded SEC 2026 Q3 Form N-PORT data-set archive. They are public SEC-derived holdings data, committed here so the return-coverage job does not need to re-download the 441 MB archive from a GitHub-hosted runner (the SEC returned HTTP 403 to that runner).

## Source filings

| Portfolio | Report date | Accession |
|---|---|---|
| AB Large Cap Value Fund, starting holdings | 2026-05-31 | `0001410368-26-074950` |
| AB Large Cap Value Fund, actual ending holdings | 2026-06-30 | `0001410368-26-086295` |
| iShares Core S&P 500 ETF (IVV), benchmark | 2026-06-30 | `0002071691-26-019760` |

The AB inputs contain 62 May common-equity positions and 60 June common-equity positions. Each file's equity weights are normalized to 100% within the reported common-equity sleeve; this does not change the as-filed percentages retained in the full pilot audit.

## IVV benchmark compression

The IVV input contains 50 rows: 49 individual securities that occur in the union of AB's May and June holdings, plus `__IVV_OTHER__`, which aggregates the remaining IVV holdings (65.6564339% of IVV's normalized equity sleeve).

This compression is mathematically exact for Active Share against both AB portfolios and the May-based no-trade portfolio: all securities outside the union have zero weight in each AB portfolio, so their combined benchmark weight contributes the same absolute-difference term as the individual holdings. The compact file is not a substitute for the full IVV holdings file for any other analysis.

## Return interval

For the May 31 starting holdings, the price anchor is the last SPY trading date on or before May 31 (expected May 29, 2026); the ending anchor is the last SPY trading date on or before June 30, 2026. The return script uses adjusted daily closes and refuses stale-price carry-forward. If any starting position lacks a return, the strict no-trade Active Share is withheld rather than calculated on a renormalized subset.

## Identity and data caveats

- Security keys are ISINs from the N-PORT IDENTIFIERS table; CUSIP is retained as a fallback field.
- Identifier rows were aggregated to one row per holding before joining, avoiding the one-to-many IDENTIFIERS fan-out.
- The benchmark is IVV's reported holdings, not official S&P 500 index weights.
- The resulting no-trade calculation is a one-interval, normalized equity-sleeve comparison. It does not claim to model fund flows, cash, derivatives, FX, delistings, mergers, or corporate actions comprehensively.
