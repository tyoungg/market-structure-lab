# Multi-fund N-PORT panel pilot

## Sample

The initial balanced panel contains 11 active U.S. large-cap mutual-fund series, selected from the SEC 2026 Q3 N-PORT release. The screening rule is at least $500 million in net assets at the June 30, 2026 observation, a U.S.-registered mutual-fund series (not an ETF or variable-insurance portfolio), and public prospectus/strategy evidence for an active large-cap equity mandate. The exact series IDs, styles, AUM screen, and evidence URLs are in `sample_funds.csv`.

This is a purposive feasibility cohort, not a representative sample. Selecting funds that exist and exceed the AUM threshold in 2026 introduces survivorship and size-selection bias. It excludes entrants and funds liquidated/merged before the selection date. The next expansion should construct the universe point-in-time and retain terminated series.

## Time window

Four quarter-end report dates:

- 2025-09-30
- 2025-12-31
- 2026-03-31
- 2026-06-30

These produce three consecutive quarterly intervals. The SEC archive partitions used are 2025 Q4 through 2026 Q3, based on source filing quarter rather than report date.

## Data source

The runner reads the public-domain SEC Form N-PORT structured data from the unofficial `trader298/sec-nport` Hugging Face Parquet mirror. It is a transformation of the SEC quarterly archives; the SEC remains authoritative. The pipeline resolves original and amended filings across all four source partitions and excludes late-filing notices (`NT NPORT-P`). The latest valid `NPORT-P` or `NPORT-P/A` filing wins for each series/report date.

A June 2026 cross-check compares the Hugging Face-derived AB Large Cap Value / IVV Active Share against the already-audited extraction from the original SEC 2026 Q3 ZIP. The job fails if the Active Share difference exceeds 1e-6.

## Calculation

For each fund and interval:

1. Select the beginning and ending N-PORT common-equity (`ASSET_CAT=EC`) holdings.
2. Aggregate the one-to-many IDENTIFIERS bridge to one row per holding before joining.
3. Normalize each common-equity sleeve to 100% and preserve the as-filed NAV percentage separately.
4. Map each starting holding to a U.S.-traded symbol with OpenFIGI (ISIN first, CUSIP fallback; documented manual overrides where already validated).
5. Retrieve Yahoo Finance auto-adjusted daily closes. Use the last SPY trading date on or before each N-PORT report date; never carry a stale price forward.
6. Compute the no-trade drifted weights and compare the no-trade and actual ending portfolios with the same-date IVV N-PORT holdings proxy.
7. Withhold the strict no-trade estimate if any starting equity position lacks a return. Coverage is reported by beginning equity weight and by position.

The main outcome is actual ending Active Share minus no-trade ending Active Share. A negative value means actual trading moved the fund's equity sleeve closer to the IVV holdings proxy than market-return drift alone; positive means farther away.

## Important limitations

- The benchmark is IVV's N-PORT holdings, not official S&P 500 weights.
- The model covers only the common-equity sleeve; cash, derivatives, shorts, and other asset classes are excluded.
- Fund flows are not allocated to individual securities; the equity-sleeve counterfactual assumes proportional treatment of flows.
- Yahoo adjusted prices and OpenFIGI are public feasibility sources, not an institutional-grade security master.
- Foreign listings, ADRs, FX, mergers, delistings, ticker changes, and corporate actions require position-level review. Incomplete return coverage blocks the strict estimate.
- Results are descriptive, not causal, and the 11-fund sample is not representative.

## Run

```bash
python scripts/run_nport_panel.py \
  --funds data/nport_panel/sample_funds.csv \
  --partitions 2025Q4 2026Q1 2026Q2 2026Q3 \
  --dates 2025-09-30 2025-12-31 2026-03-31 2026-06-30 \
  --output-dir data/nport_panel_output
```

The workflow uploads the panel outputs as a GitHub Actions artifact. No paid data source is used.
