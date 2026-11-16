# No-Trade Counterfactual: Large-Cap Fund Study

## Purpose

Estimate how much a fund's portfolio composition would have changed between two public reporting dates if the manager had made no trades, then compare that mechanically drifted portfolio with the fund's reported ending portfolio.

This is a descriptive counterfactual. It does **not** identify manager intent, skill, or the causal effect of trading.

## Initial scope

- **Fund universe:** actively managed U.S. large-cap equity mutual funds.
- **Primary holdings source:** SEC Form N-PORT public data sets.
- **Observation frequency:** quarterly public snapshots.
- **Initial data window:** October 2019 through the latest complete SEC public dataset.
- **Benchmark candidate:** S&P 500, subject to a public historical constituent-and-weight feasibility check.
- **Secondary samples:** ETFs and 13F manager portfolios are out of scope for the first pass. They may be added later as separately identified samples.

Large-cap and active-management labels are not assumed to be clean fields in N-PORT. Candidate fund classification must be documented and reviewed rather than inferred solely from current fund names or current survival.

## Core comparison

For each fund and consecutive pair of reporting dates:

1. **Actual ending portfolio:** positions reported by the fund at the ending date, converted to portfolio weights using the reported portfolio net assets and a clearly documented holdings scope.
2. **No-trade ending portfolio:** beginning-date positions carried forward using security total returns and corporate actions, with no manager purchases or sales.
3. **Benchmark:** the same ending-date benchmark composition and weights are used when evaluating both portfolios.

For a fully invested portfolio with no cash-flow or corporate-action complications, the weight of security *i* in the no-trade portfolio is:

\[
w^{NT}_{i,t+1} =
\frac{w_{i,t}(1+r_{i,t+1})}
{\sum_j w_{j,t}(1+r_{j,t+1})}
\]

This formula is a starting identity, not permission to ignore cash, flows, derivatives, corporate actions, delistings, or missing returns. The implementation must account for those items or explicitly exclude the affected interval from the primary estimate and report the exclusion.

## Primary metric

Active Share:

\[
AS(P,B) = \frac{1}{2}\sum_i |w_{P,i}-w_{B,i}|
\]

Calculate:

- Actual Active Share at the ending date.
- No-trade Active Share at the ending date.
- **Trading-associated Active Share difference** = actual Active Share minus no-trade Active Share.

Interpretation of the signed difference:

- Negative: actual trading left the portfolio closer to the benchmark than the no-trade portfolio.
- Positive: actual trading left the portfolio farther from the benchmark than the no-trade portfolio.

This difference is descriptive, not causal. It can reflect manager decisions, fund flows, corporate actions, data limitations, and the definition of the investable portfolio.

Also report the change from beginning-date Active Share to ending-date no-trade Active Share as mechanical drift. Because the primary comparison uses the ending-date benchmark for both ending portfolios, benchmark reconstitution does not mechanically differ between the actual and no-trade comparison.

## Universe construction

Build a candidate registry at the fund-series level, not just by ticker or fund family.

For every candidate retain:

- SEC registrant CIK, series ID, and class/contract ID where available.
- Fund name and reporting period.
- Legal structure (mutual fund / ETF / other).
- Investment objective and strategy evidence.
- Benchmark named in public fund documents.
- Evidence supporting U.S. equity and large-cap classification.
- Evidence supporting active rather than index-tracking management.
- Inclusion/exclusion decision, reason, reviewer, and date.

Initial inclusion rule to test: a U.S. domestic equity strategy whose stated mandate is large-cap or whose stated benchmark is the S&P 500 or a closely related large-cap index, and whose mandate is actively managed. Do not classify a fund as active merely because its reported holdings differ from the index.

Retain dead, merged, liquidated, and renamed funds when historical filings permit. Do not construct the sample from today's surviving fund list alone.

## Data sources and limitations

### SEC Form N-PORT

Use the SEC's quarterly public bulk datasets as the authoritative starting point. N-PORT is a fund-level source with position-level holdings and stable fund/security identifiers in many records. It is materially better suited to this question than 13F.

The SEC currently describes its public bulk dataset as quarterly and says it contains only filings already disseminated. The filings themselves report monthly portfolio information, but that does not mean every monthly portfolio is currently available to the public in the bulk data. Preserve filing date and report-period date separately.

Treat the SEC's flattened data as an extraction convenience, not ground truth. Keep accession numbers and validate a sample of records against original filings. Handle amendments and duplicate submissions explicitly.

### Benchmark

Do not use current S&P 500 membership for historical periods. Do not use equal-weighted constituent snapshots as if they were cap-weighted index weights.

First investigate whether historical S&P 500 constituents and weights can be reconstructed consistently from freely available primary or issuer-published records. A tracking ETF's disclosed holdings can be used as a clearly labeled proxy if historical holdings are obtainable and coverage is adequate; it is not the official index itself. Record source, date, identifier, weight, and any tracking difference.

If reliable public historical weights cannot be obtained, the initial pilot may report fund portfolio drift and turnover-related diagnostics without claiming benchmark Active Share. Do not silently substitute a current or equal-weighted benchmark.

### Security returns and identifiers

Prefer stable identifiers such as CUSIP/ISIN plus issuer/security metadata; ticker alone is insufficient because tickers change and are reused.

Investigate freely available total-return data with delisted-security coverage. Adjusted prices from a public market-data API may be used for a prototype only after documenting survivorship, corporate-action, symbol-mapping, and missing-return limitations. Never silently drop a missing or delisted security.

## Holdings treatment

- Start with common equity positions relevant to a domestic large-cap equity strategy.
- Separately identify cash, cash equivalents, derivatives, short positions, securities lending, and non-equity assets.
- Do not normalize an equity-only subset to 100% without showing how much of fund NAV it represents.
- Define whether weights use fund net assets or the value of the selected equity sleeve.
- Reconcile reported holdings and assets to fund-level totals; flag material unexplained differences.
- Resolve stock splits, mergers, spin-offs, tender offers, distributions, and delistings in the no-trade path.
- Explicitly account for cash and fund flows. If the available data cannot support an adjustment, label the assumption and show sensitivity rather than implying exact reconstruction.

## Phase 0: feasibility and validation (first deliverable)

Before building a full panel:

1. Download and inspect one recent SEC N-PORT quarterly archive and its metadata/readme.
2. Identify the exact tables, join keys, fields, and filing/report dates needed for fund and holding records.
3. Build a candidate list of active U.S. large-cap mutual fund series and document the classification method.
4. Select a small pilot: several funds with consecutive public filings, including at least one fund that merged, closed, or changed name if feasible.
5. Test whether historical S&P 500 proxy holdings and weights can be retrieved for the same dates.
6. Test stable security matching and total-return coverage for the pilot holdings.
7. Reconcile at least one fund-period against its original SEC filing.

### Phase 0 acceptance tests

Do not scale until all are true for the pilot:

- Fund series and reporting dates are identified consistently across filings.
- Amendments and duplicate filings are handled deterministically.
- Position-level values reconcile reasonably to reported fund totals, with differences explained.
- No-trade weights reconcile to the modeled portfolio value; missing/delisted holdings are not silently removed.
- Corporate actions are applied or the interval is explicitly excluded.
- Actual and no-trade portfolios use the same ending-date benchmark weights.
- Active Share can be independently recalculated from the exported weights.
- Every exclusion and unresolved data issue is retained in an audit table.

## Phase 1: panel construction (only after Phase 0 passes)

Build a fund-quarter panel containing fund identifiers, classification evidence, report and filing dates, holdings coverage, actual weights, no-trade weights, benchmark source/coverage, Active Share metrics, and data-quality flags.

Report distributions and coverage before estimating trends. Show results by fund and time, and distinguish within-fund changes from changes in sample composition.

## Required sensitivity analyses

- Strict versus broad large-cap classification.
- S&P 500 benchmark proxy versus alternative large-cap benchmark where supportable.
- Equity sleeve weights versus total-NAV weights.
- Exclusion versus conservative treatment of holdings with missing returns.
- Survivors only versus all historically observable funds.
- Results with and without funds with material derivatives, cash, or non-equity exposures.

## Guardrails

- Do not describe the trading-associated difference as a causal estimate of manager skill or intent.
- Do not combine N-PORT fund portfolios and 13F manager portfolios in one undifferentiated sample.
- Do not infer that a fund is active from holdings divergence alone.
- Do not use current holdings, current fund classifications, or current constituents to fill historical gaps without labeling the look-ahead.
- Preserve raw source files or reproducible download references, accession numbers, transformation logs, and data-quality flags.
