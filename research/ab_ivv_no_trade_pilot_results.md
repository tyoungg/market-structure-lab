# AB Large Cap Value / IVV no-trade return pilot — results

**Status: strict no-trade estimate calculated.** The return pipeline obtained adjusted returns for all 62 beginning common-equity positions, covering 99.99999995% of the normalized starting equity sleeve (rounding residual only).

## Result

| Measure | Result |
|---|---:|
| AB beginning common-equity positions | 62 |
| Positions with resolved ticker | 62 / 62 |
| Positions with valid adjusted return | 62 / 62 |
| Beginning equity-weight return coverage | 100.0000% |
| AB actual June 30 Active Share vs IVV holdings proxy | 77.1753% |
| AB no-trade June 30 Active Share vs IVV holdings proxy | 81.3786% |
| Actual minus no-trade Active Share | **-4.2033 percentage points** |

The sign is important: actual AB holdings at June 30 were about 4.20 percentage points closer to IVV's reported holdings than the return-drift-only counterfactual. This is a one-fund, one-interval descriptive result. It is not evidence that the manager intended to track the index, that the trades were skillful, or that the same relationship holds across managers or periods.

## Construction

- Starting portfolio: AB Large Cap Value Fund, N-PORT report date 2026-05-31, accession `0001410368-26-074950`.
- Actual ending portfolio: AB Large Cap Value Fund, N-PORT report date 2026-06-30, accession `0001410368-26-086295`.
- Benchmark: IVV, N-PORT report date 2026-06-30, accession `0002071691-26-019760`.
- The starting portfolio has 62 common-equity positions. The starting and ending equity sleeves are normalized to 100% for this Active Share calculation; reported all-asset weights remain available in the original pilot audit.
- Daily adjusted closes were sourced from Yahoo Finance. The return window uses the last SPY trading date on or before each N-PORT report date (May 29, 2026 through June 30, 2026). No stale-price carry-forward was used.
- Identifiers were mapped with OpenFIGI (ISIN first, CUSIP fallback), plus the source-documented ticker overrides in `data/nport_pilot_inputs/ticker_overrides.csv`. Overrides resolve symbols only; they do not supply or impute prices.
- IVV's reported holdings are a tracker-fund proxy for the S&P 500, not official index constituent weights. The compact IVV file retains each IVV security in the union of AB's May and June holdings and combines the remaining IVV names into `__IVV_OTHER__`; this preserves the Active Share arithmetic for both portfolios.

## Interpretation and limitations

The no-trade counterfactual applies each starting security's adjusted return to its beginning equity weight, then renormalizes the resulting equity sleeve. It therefore isolates return drift from the change in reported weights, under the simplifying assumption that flows do not alter relative security weights within the sleeve.

This remains a pilot, not the final panel methodology. Important caveats:

1. Yahoo Finance adjusted prices and OpenFIGI are public feasibility sources, not an institutional-grade security master or authoritative total-return database.
2. Corporate actions, mergers, delistings, foreign-exchange exposures, and ticker changes need explicit position-level validation before scaling.
3. Cash and derivatives are excluded from the normalized equity-sleeve Active Share.
4. IVV is a tracker-fund holdings proxy, not official S&P 500 index weights.
5. The observed difference is descriptive and cannot be interpreted causally.

## Reproducibility

- Inputs and provenance: `data/nport_pilot_inputs/`
- Return runner: `scripts/run_nport_return_coverage.py`
- Mapping and price logic: `scripts/run_nport_pilot.py`
- Tests: `tests/test_nport_pilot.py`
- Latest passing run: [GitHub Actions run 18](https://github.com/tyoungg/market-structure-lab/actions/runs/44104690519)
- Run artifact (returns, coverage audit, no-trade weights, JSON summary): [Download AB / IVV return-coverage artifact](https://github.com/tyoungg/market-structure-lab/actions/runs/44104690519/artifacts/14338621493)
