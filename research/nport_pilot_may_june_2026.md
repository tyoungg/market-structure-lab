# N-PORT pilot extraction — AB Large Cap Value vs. IVV

**Run date:** 2026-11-17  
**Source:** uploaded SEC `2026q3_nport.zip` archive  
**Pilot interval:** 2026-05-31 to 2026-06-30  
**Status:** holdings extraction and benchmark comparison passed; security-return matching and no-trade calculation not yet run.

## Why this pair

The SEC filing for AB Large Cap Value Fund (series `S000010411`) contains consecutive May 31 and June 30, 2026 observations in the uploaded archive. Its February 28, 2026 summary prospectus says the fund invests in large-cap equities selected using the adviser's fundamental value approach, normally holds at least 80% of net assets in large-cap equity securities, and is actively managed. The SEC's 2024 supplement documents the name change from AB Value Fund to AB Large Cap Value Fund effective around October 1, 2024. This is a documented active large-cap candidate, not a name-only classification.

For June 30, the pilot uses iShares Core S&P 500 ETF (IVV), series `S000004310`. Its prospectus says it seeks to track the S&P 500. Its N-PORT holdings are a **tracker-fund proxy**, not official index weights.

## Filing observations selected

| Portfolio | Report date | Filing date | Form | Accession | Net assets |
|---|---|---|---|---|---:|
| AB Large Cap Value | 2026-05-31 | 2026-07-24 | NPORT-P | `0001410368-26-074950` | $507.99m |
| AB Large Cap Value | 2026-06-30 | 2026-08-26 | NPORT-P | `0001410368-26-086295` | $529.40m |
| iShares Core S&P 500 ETF | 2026-06-30 | 2026-08-25 | NPORT-P | `0002071691-26-019760` | $888.13bn |

There is one filing in each selected series/report-date group in this archive. The selected records are originals, not amendments. This does not replace amendment resolution across all quarterly archives.

## Holdings reconciliation

| Measure | AB May 31 | AB June 30 | IVV June 30 |
|---|---:|---:|---:|
| All reported holding rows | 64 | 62 | 508 |
| Common-equity (`EC`) rows | 62 | 60 | 503 |
| Common equity as % of NAV | 99.33% | 98.61% | 99.83% |
| All reported holding percentages summed | 100.43% | 100.19% | 100.12% |

The sums slightly above 100% are retained as filed, not silently rescaled. Each common-equity holding in this pilot has one unambiguous ISIN after identifier aggregation. The identifier table is one-to-many; it must never be joined raw to holdings before summing weights.

## Preliminary same-date Active Share

Using common-equity holdings only, matching securities by ISIN, and normalizing each equity sleeve to 100%:

**AB Large Cap Value vs. IVV tracker-fund proxy on June 30, 2026: 77.18% Active Share.**

- AB common-equity holdings: 60
- IVV common-equity holdings: 503
- Shared securities: 45
- AB securities not found in IVV: 15
- IVV securities not found in AB: 458

This is a single-date equity-sleeve comparison against an S&P 500 tracker fund. It is not official S&P 500 Active Share and says nothing by itself about manager trading, skill, or the no-trade counterfactual.

## What changed between AB's two reported portfolios

The May and June portfolios share 57 security identifiers. Five May positions do not appear in June; three June positions do not appear in May. The half-L1 distance between the two normalized equity-sleeve weight vectors is 15.01 percentage points. This is **not turnover**: it combines price-driven weight drift, purchases/sales, corporate actions, and any unresolved identifier differences. It is not a no-trade estimate.

AB's reported net assets rose 4.21% between the two observations. This combines investment performance and shareholder flows; it is not a measure of net inflows.

## No-trade counterfactual status

**Not calculated yet.** N-PORT does not provide security-level total returns to advance each May holding to June 30. The pilot script now has an optional public-data path:

1. Map ISIN/CUSIP to a U.S.-listed instrument using OpenFIGI's free public mapping API.
2. Retrieve dividend- and split-adjusted daily prices from Yahoo Finance.
3. Use the common market calendar to select the last trading date on or before each N-PORT report date.
4. Refuse to carry stale prices across missing dates. If any beginning equity position lacks a validated return, do not report the strict no-trade estimate.
5. Calculate no-trade weights only at 100% beginning equity-weight return coverage. Foreign-listed securities, FX conversion, delistings, mergers, and corporate actions remain explicit blockers unless independently resolved.

The 100% requirement is deliberately conservative for this first pilot. If coverage is incomplete, report coverage and investigate unmatched securities; do not renormalize a subset and present it as the whole portfolio.

The no-trade calculation is an equity-sleeve model. It assumes fund-level flows are treated proportionally within the equity sleeve; N-PORT does not identify which individual securities were traded to meet flows. Cash, derivatives, and other non-equity positions remain in the raw export and are not silently folded into the equity-only calculation.

## Reproducibility

The script is `scripts/run_nport_pilot.py`. Example:

```bash
python scripts/run_nport_pilot.py \
  --archive /path/to/2026q3_nport.zip \
  --active-series S000010411 \
  --benchmark-series S000004310 \
  --start-date 2026-05-31 \
  --end-date 2026-06-30
```

Add `--fetch-returns` to invoke the public OpenFIGI + Yahoo Finance path. This requires network access and the installed `requests` and `yfinance` packages. Outputs include raw selected holdings, filing-resolution audit, active and tracker equity weights, and a JSON summary. With complete return coverage, it also writes security returns and no-trade ending weights.

Three synthetic unit tests cover Active Share, no-trade weight arithmetic, and the rule that incomplete return coverage blocks the strict estimate. The offline extraction was run against the uploaded archive and reproduced the figures above.

## Sources

- SEC Form N-PORT public data sets: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
- AB Large Cap Value Fund summary prospectus (Feb. 28, 2026): https://www.sec.gov/Archives/edgar/data/1129870/000119312526077180/d102870d497k.htm
- AB Value Fund strategy/name-change supplement (Aug. 1, 2024): https://www.sec.gov/Archives/edgar/data/1129870/000091957424004199/d11407846_497.htm
- iShares Core S&P 500 ETF prospectus: https://www.ishares.com/us/library/stream-document?documentId=925833~2410979~2246030~2379322~2306176~2258139~2251621~2177662~2128795&iframeUrlOverride=/us/literature/summary-prospectus/sp-ishares-core-s-and-p-500-etf-3-31.pdf&product=I-SP500&shareClass=NA&stream=reg
- OpenFIGI API documentation: https://www.openfigi.com/api/documentation
- yfinance price-history documentation: https://ranaroussi.github.io/yfinance/reference/yfinance.price_history.html
