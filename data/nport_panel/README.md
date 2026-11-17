# Multi-fund N-PORT panel pilot

## Relationship to The Rational Coward

This panel supports the addendum's **no-trade drift counterfactual** workstream. It tests whether observed active-fund holdings moved closer to or farther from a same-date S&P 500 tracker proxy than mechanical return drift alone would imply.

It does not establish the addendum's broader thesis, identify manager intent, or replace the historical active-only Active Share and provider-bridge work. The cohort is a purposive feasibility sample, not a representative universe. The addendum's sensitivity findings remain binding guardrails: the historical asset-weighted Active Share slope changes from approximately -0.43 pp/year at a 5% floor to approximately -0.03 pp/year at a 20% floor, and the earlier 83% reallocation claim must not be described as an active-only result.

## Sample and selection limitation

The initial manifest contains 11 active U.S. large-cap mutual-fund series, selected from the SEC 2026 Q3 N-PORT release. The screen requires at least $500 million in net assets at the June 30, 2026 observation, a U.S.-registered mutual-fund series, and public prospectus/strategy evidence for an active large-cap equity mandate. Series IDs, styles, assets and evidence URLs are in `sample_funds.csv`.

This is a purposive, size-selected and survivorship-biased cohort. It excludes funds that disappeared before the latest release and entrants that did not meet the 2026 size screen. It cannot support population-level claims about active managers.

## Time window and report-date selection

The source partitions are 2025 Q4 through 2026 Q3, based on the SEC data-set partition, not a hard-coded report date.

The runner now:
- reads all valid report dates for the selected series in those partitions;
- selects the latest valid `NPORT-P` or `NPORT-P/A` filing for each series/report-date pair;
- excludes `NT NPORT-P` late-filing notices;
- constructs intervals between each fund's own consecutive observed report dates;
- requires an IVV holdings observation on the exact same ending report date;
- flags gaps over 150 days and missing same-date benchmark observations instead of silently substituting calendar quarter ends.

The default report-date window is 2025-07-01 through 2026-09-30. The window deliberately starts before September 2025 so the runner does not discard earlier report dates contained in the 2025 Q4 source partition. The observed dates and selected accession metadata are published in `observation_availability.csv` and `filing_resolution.csv`.

## Data source and holdings extraction

The runner reads public-domain SEC Form N-PORT structured data from the unofficial `trader298/sec-nport` Hugging Face Parquet mirror. The SEC remains authoritative. The June 2026 AB Large Cap Value / IVV extraction is cross-checked against the previously audited original SEC ZIP pilot; the job fails if the Active Share difference exceeds 1e-6.

The one-to-many N-PORT `IDENTIFIERS` bridge is aggregated to one row per holding before joining. Common-equity (`ASSET_CAT=EC`) positions are normalized within the equity sleeve, while as-filed NAV percentages remain separate.

## Security crosswalk and return evidence

For each starting security, the pipeline preserves:
- permanent identifier candidates (ISIN/CUSIP), N-PORT-reported ticker and issuer name;
- any ticker candidate chosen from N-PORT, OpenFIGI or a documented override;
- mapping source and OpenFIGI candidate details;
- endpoint adjusted prices, dates and Yahoo Finance price status;
- conflicting ticker/name candidates when the same security key appears in more than one starting portfolio.

N-PORT-reported tickers are now used as explicit candidates instead of being ignored. When multiple funds report conflicting tickers for the same security key, the shared cross-fund candidate builder does not silently choose one. OpenFIGI is a candidate generator, not an authoritative security master.

**Important distinction:** the current crosswalk is candidate/unreviewed. A ticker plus two endpoint prices is not proof that the price series represents the exact security/share class held by the fund. The pipeline therefore labels complete-price-coverage calculations as provisional until security identity, share class, venue, FX and corporate-action treatment are reviewed. Raw adjusted endpoint prices and dates are retained to make that review possible.

The generated `security_crosswalk.csv` is a review queue and should not be hand-edited as the durable approval record. The durable review files are [`security_crosswalk_review_ledger.csv`](security_crosswalk_review_ledger.csv) and [`SECURITY_REVIEW_PROTOCOL.md`](SECURITY_REVIEW_PROTOCOL.md). The ledger is seeded from a published crosswalk snapshot; preserve reviewer decisions when refreshing it. No mapping is approved by default.

## Counterfactual calculation

For each interval:
1. Advance every starting common-equity holding by its adjusted-price return:
   `w_nt = w_start * (1 + return)`, normalized within the modeled equity sleeve.
2. Compare actual ending Active Share and no-trade ending Active Share with the same-date IVV N-PORT holdings proxy.
3. Report actual ending Active Share minus no-trade ending Active Share.
4. Withhold the price-coverage estimate if any starting equity position lacks an endpoint return.

Negative differences mean actual trading moved the equity sleeve closer to the IVV tracker proxy than return drift alone; positive differences mean farther away.

## Important limitations

- IVV is a tracker-fund proxy, not official S&P 500 constituent weights.
- Only the common-equity sleeve is modeled; cash, derivatives, shorts and other asset classes are excluded.
- Fund flows are not allocated to individual securities; the equity-sleeve counterfactual assumes proportional treatment of flows.
- Yahoo adjusted prices and OpenFIGI are public feasibility sources, not an institutional-grade security master.
- Foreign listings, ADRs, FX, mergers, delistings, ticker changes and corporate actions require position-level review.
- Current mappings are candidate/unreviewed. Complete endpoint-price coverage is not equivalent to validated security identity.
- Results are descriptive, not causal.
- The 11-fund cohort is not representative and should not be pooled with Notre Dame or CRSP historical series without a separate provider bridge.

## Run

```bash
python scripts/run_nport_panel.py \
  --funds data/nport_panel/sample_funds.csv \
  --partitions 2025Q4 2026Q1 2026Q2 2026Q3 \
  --start-date 2025-07-01 \
  --end-date 2026-09-30 \
  --output-dir data/nport_panel_output
```

The GitHub Actions workflow publishes compact dashboard files and a 30-day full-output artifact. No paid data source is used.
