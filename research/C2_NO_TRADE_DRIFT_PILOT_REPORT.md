# C.2 No-Trade Drift Pilot — Results

**Branch:** `RUSSEL_SP`  
**Workflow:** [run 45029952352](https://github.com/tyoungg/market-structure-lab/actions/runs/45029952352)  
**Artifact:** [`c2-no-trade-drift-pilot`, ID 14757665853](https://github.com/tyoungg/market-structure-lab/actions/runs/45029952352/artifacts/14757665853)  
**Fund:** Optimum Large Cap Growth Fund, CIK 0001227523, series S000002422  
**Period:** 2025-06-30 through 2025-09-30

## Executive result

The first public-data no-trade drift pilot completed. Six SEC N-PORT-P filings (fund, SPY, and IWB at both dates) passed report-date and entity/series checks. The parser extracted 3,294 positions, including 3,276 common-equity positions.

The calculation used common-equity weights normalized within each equity sleeve, aggregated duplicate CUSIPs, and grew the June 30 fund holdings using dividend- and split-adjusted security returns. It then compared the drifted portfolio with actual September 30 holdings and with both benchmark ETF proxies.

The pilot passed its 95% price-coverage gate: **99.923363% of starting equity value** had endpoint prices. One listed ticker (EXAS) and two non-ticker positions (ABIOMED CVR and Magic Leap) were retained with a zero-return assumption. Together they represent **0.076637%** of starting equity value. The result is therefore calculated, but this residual assumption is disclosed and should be tested in a sensitivity run before expanding the sample.

## Active Share decomposition

All values are percentages of the common-equity sleeve. Components are percentage-point changes in Active Share.

| Measure | SPY (S&P 500 ETF proxy) | IWB (Russell 1000 ETF proxy) |
|---|---:|---:|
| Actual Active Share, June 30 | 52.031% | 54.738% |
| No-trade Active Share at September 30 vs. frozen June benchmark | 52.027% | 54.743% |
| No-trade Active Share at September 30 vs. September benchmark | 50.012% | 52.952% |
| Actual Active Share, September 30 | 49.634% | 52.800% |
| Fund price-drift component | -0.005 pp | +0.006 pp |
| Benchmark-weight-change component | -2.015 pp | -1.791 pp |
| Actual-portfolio-change-beyond-drift component | -0.378 pp | -0.152 pp |
| Component reconciliation error | 0.000 pp | 0.000 pp |
| Actual-versus-no-trade portfolio distance at September 30 | 13.200% | 13.200% |

The decomposition is ordered: first grow the fund's June holdings by their security returns against the frozen June benchmark; next substitute the September benchmark weights; finally compare the actual September fund portfolio with the no-trade portfolio. The three components reconcile exactly to the actual Active Share change.

## Interpretation

1. **Fund price drift barely changed Active Share in this quarter.** The no-trade portfolio's Active Share against the frozen benchmark moved by approximately -0.005 percentage points for SPY and +0.006 points for IWB.
2. **Benchmark weight changes account for most of the observed Active Share decline.** Replacing the June ETF weights with September ETF weights reduced measured Active Share by about 2.015 points versus SPY and 1.791 points versus IWB.
3. **The actual September portfolio differs materially from the no-trade portfolio, even though the Active Share impact is smaller.** The one-way distance between actual and drifted fund weights is 13.200% of the equity sleeve. The Active Share effect of this portfolio change is -0.378 points versus SPY and -0.152 points versus IWB.
4. This is not a causal estimate of manager trading or turnover. The actual-versus-no-trade gap can also reflect flows, corporate actions, security mapping, cash/derivative changes, and reporting conventions.

## Data and method limitations

- SPY and IWB are ETF holdings proxies, not official S&P 500 or Russell 1000 index constituent/weight files. Tracking, sampling, cash, derivatives, and securities lending can create differences.
- N-PORT reports are aligned by `repPdDate`, not filing date.
- CUSIP is the primary matching key; ISIN is the fallback. Duplicate CUSIPs are aggregated. The name-only Magic Leap position remains a unique, unmatched security.
- Yahoo Finance adjusted close was retrieved through `yfinance 1.8.0`. The package is not affiliated with or endorsed by Yahoo, and its documentation directs users to Yahoo's data terms. This is an exploratory public-data price source, not a licensed institutional return database.
- EXAS had no available Yahoo endpoint prices for this period. ABIOMED CVR and Magic Leap had no ticker. All three were carried at zero return; their combined starting weight is 0.076637%.
- This is one fund and one three-month interval. It establishes technical feasibility, not a general empirical result. The 2025 sample is separate from the 1979–2023 TR/CRSP Active Share panel and must not be pooled with it.

## Next research step

Run a predeclared multi-fund cohort across several consecutive quarter transitions. Select funds based on documented active strategies and N-PORT availability, not on observed results or survival. Retain the same data-quality gates, benchmark-proxy caveats, and no-trade decomposition. Add an explicit sensitivity for the small unpriced position weight before scaling.
