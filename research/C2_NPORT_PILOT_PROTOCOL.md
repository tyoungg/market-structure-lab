# C.2 Public N-PORT No-Trade Drift Pilot Protocol

**Branch:** `RUSSEL_SP`  
**Status:** Completed one-fund, one-quarter public-data no-trade drift pilot  
**Scope:** One active fund, two consecutive quarter-end portfolios, two ETF benchmark proxies. This is a method-feasibility sample, not a representative empirical sample.

## 1. Pilot sample

Fund selected from the manually reviewed C.1 active series:

- **Optimum Large Cap Growth Fund**
- SEC CIK: `0001227523`
- SEC series: `S000002422`
- Filing/series identity was manually linked in C.1; the 2025 prospectus describes active multi-subadviser security selection.

Two quarter-end holdings dates:

- 2025-06-30
- 2025-09-30

Benchmark proxies, using SEC N-PORT holdings at the same dates:

- **SPY** — SPDR S&P 500 ETF Trust; S&P 500 proxy
- **IWB** — iShares Russell 1000 ETF; Russell 1000 proxy

The ETF holdings are investable proxies, not the official index constituent/weight files. Tracking differences, cash, derivatives, sampling, and securities lending may affect the comparison.

## 2. Frozen SEC source filings

All six source files are public SEC Form N-PORT-P XML filings. The XML `repPdDate` is the portfolio valuation date; the filing date is not used as the holdings date.

| Entity | Holdings date | CIK | Series ID | Accession |
|---|---|---|---|---|
| Optimum Large Cap Growth Fund | 2025-06-30 | 0001227523 | S000002422 | 0001752724-25-207530 |
| Optimum Large Cap Growth Fund | 2025-09-30 | 0001227523 | S000002422 | 0000940400-25-009486 |
| SPY | 2025-06-30 | 0000884394 | UIT trust | 0001752724-25-211156 |
| SPY | 2025-09-30 | 0000884394 | UIT trust | 0001410368-25-031962 |
| IWB | 2025-06-30 | 0001100663 | S000004347 | 0001752724-25-204367 |
| IWB | 2025-09-30 | 0001100663 | S000004347 | 0001004726-25-002043 |

Primary XML URLs (the adjacent SEC filing-index pages provide the registrant/series metadata used for independent identity checks):

- [Optimum 2025-06-30](https://www.sec.gov/Archives/edgar/data/1227523/000175272425207530/primary_doc.xml)
- [Optimum 2025-09-30](https://www.sec.gov/Archives/edgar/data/1227523/000094040025009486/primary_doc.xml)
- [SPY 2025-06-30](https://www.sec.gov/Archives/edgar/data/884394/000175272425211156/primary_doc.xml)
- [SPY 2025-09-30](https://www.sec.gov/Archives/edgar/data/884394/000141036825031962/primary_doc.xml)
- [IWB 2025-06-30](https://www.sec.gov/Archives/edgar/data/1100663/000175272425204367/primary_doc.xml)
- [IWB 2025-09-30](https://www.sec.gov/Archives/edgar/data/1100663/000100472625002043/primary_doc.xml)

The acquisition workflow must validate the expected report date and fund/series identity from the XML before accepting a file. SPY is a unit investment trust; its N-PORT XML reports `N/A` in the series/registrant name fields. Its identity is validated using the SEC filing-index registrant CIK/name, the accession path CIK, and the report date rather than a series ID. The parser records this distinct validation method rather than treating `N/A` as a name match.

## 3. Initial acquisition output

The first C.2 workflow is limited to reproducible acquisition and XML parsing. It must:

1. Download all six XML files with an SEC-compliant `User-Agent` using the repository's `SEC_CONTACT_EMAIL` secret.
2. Retain the original XML files in the workflow artifact only; do not commit raw filings.
3. Validate the two report dates for each entity and the expected Optimum/IWB series IDs.
4. Extract filing metadata, `repPdDate`, `seriesId`, `seriesName`, `netAssets`, and every `invstOrSec` position.
5. Preserve security name/title, CUSIP, ISIN, any ticker/other identifier, asset category, payoff profile, market value, and reported percent of net assets.
6. Produce all-position and common-equity CSVs plus a per-report quality summary.

The parser must not silently drop positions with missing CUSIP or ticker. Missing identifiers and excluded asset categories must be reported with market-value weights.

## 4. Acquisition result (validated)

The successful acquisition run [45029457183](https://github.com/tyoungg/market-structure-lab/actions/runs/45029457183) uploaded artifact [14756678178](https://github.com/tyoungg/market-structure-lab/actions/runs/45029457183/artifacts/14756678178). All six reports passed date/identity validation and yielded 3,294 positions, including 3,276 common-equity positions.

| Entity | Date | Positions | Common equity | Equity weight (% NAV) | CUSIP coverage (% equity) | ISIN coverage (% equity) |
|---|---|---:|---:|---:|---:|---:|
| Optimum Large Cap Growth | 2025-06-30 | 131 | 126 | 99.503 | 100.000 | 99.9998 |
| Optimum Large Cap Growth | 2025-09-30 | 122 | 117 | 99.829 | 100.000 | 99.9995 |
| SPY | 2025-06-30 | 504 | 504 | 99.983 | 100.000 | 100.000 |
| SPY | 2025-09-30 | 503 | 503 | 99.990 | 100.000 | 100.000 |
| IWB | 2025-06-30 | 1,019 | 1,015 | 99.836 | 100.000 | 100.000 |
| IWB | 2025-09-30 | 1,015 | 1,011 | 99.822 | 100.000 | 100.000 |

Optimum's common-equity holdings contain 145 distinct ticker symbols across both dates. Two very small positions lack tickers at each date: ABIOMED CVR and Magic Leap. Together they represent approximately 0.001% of the starting equity sleeve. They will be retained with a zero-return assumption and explicitly disclosed, rather than silently dropped. SPY and IWB have no ticker field in their N-PORT XML, but every common-equity position has a CUSIP and ISIN, which is sufficient for holdings-weight matching.

Duplicate CUSIPs are present (Optimum: 10 duplicate rows per date; SPY: 25; IWB: none). The return/Active Share calculation must aggregate duplicate CUSIPs before computing weights.

## 5. No-trade drift calculation specification

After the acquisition and identity checks pass:

- Aggregate duplicate positions by security identifier before calculating weights.
- Define common equity positions as N-PORT asset category `EC` with long payoff profile. Retain other asset categories separately for reconciliation.
- Compute actual equity-only Active Share at each date:

[
AS_t = \frac{1}{2}\sum_i |w_{fund,i,t}-w_{benchmark,i,t}|
]

  Weights are normalized to 100% of the common-equity sleeve. Also report the sleeve's percent of net assets so the cash/non-equity allocation is not hidden.
- Map CUSIPs/ISINs to stable traded tickers or identifiers using a documented public mapping source. Retain one-to-many and unmapped cases; do not guess.
- Use dividend- and split-adjusted security total returns from 2025-06-30 through 2025-09-30 to grow the June fund holdings without trades:

[
w^{NT}_{i,t1}=\frac{w_{i,t0}(1+r_i)}{\sum_j w_{j,t0}(1+r_j)}
]

- Compare the no-trade portfolio at September 30 with actual Optimum holdings and with the September 30 SPY and IWB proxy portfolios.
- Report the decomposition separately:
  - starting actual Active Share;
  - no-trade fund price drift against the frozen starting benchmark;
  - benchmark weight/reconstitution change;
  - actual-versus-no-trade portfolio gap at the end date.

The final gap is not a causal estimate of manager trading. It can also reflect flows, corporate actions, derivatives, cash, reporting conventions, and data-mapping errors.

## 6. Data-quality gates

Do not publish a drift estimate unless:

- all six filings pass date and identity validation;
- the equity holdings reconcile to reported N-PORT values within documented tolerances;
- at least 95% of the starting fund equity market value has valid total-return coverage;
- at least 99% of each endpoint fund/benchmark equity value is mapped to a stable security identifier;
- duplicate, short, derivative, and non-equity positions are handled explicitly;
- the benchmark is labeled as an ETF proxy, not an official index portfolio.

If a gate fails, publish the acquisition/coverage audit only and state why the drift estimate is withheld.

## 8. First no-trade drift result

The end-to-end run [45029952352](https://github.com/tyoungg/market-structure-lab/actions/runs/45029952352) completed successfully and uploaded artifact [14757665853](https://github.com/tyoungg/market-structure-lab/actions/runs/45029952352/artifacts/14757665853). The generated report is version-controlled at [`C2_NO_TRADE_DRIFT_PILOT_REPORT.md`](C2_NO_TRADE_DRIFT_PILOT_REPORT.md).

The price coverage gate passed: **99.923363%** of starting equity value had adjusted endpoint prices. One listed ticker (EXAS) and two non-ticker positions (ABIOMED CVR and Magic Leap) were carried at zero return. Their combined starting weight is **0.076637%** of the equity sleeve. This is disclosed in the output; it is not silently imputed as observed performance.

| Measure | SPY proxy | IWB proxy |
|---|---:|---:|
| Actual Active Share, June 30 | 52.031% | 54.738% |
| No-trade Active Share at September 30 vs. frozen June benchmark | 52.027% | 54.743% |
| No-trade Active Share at September 30 vs. September benchmark | 50.012% | 52.952% |
| Actual Active Share, September 30 | 49.634% | 52.800% |
| Fund price-drift component | -0.005 pp | +0.006 pp |
| Benchmark-weight-change component | -2.015 pp | -1.791 pp |
| Actual-portfolio-change-beyond-drift component | -0.378 pp | -0.152 pp |
| Reconciliation error | 0.000 pp | 0.000 pp |
| Actual-versus-no-trade portfolio distance | 13.200% | 13.200% |

The decomposition is ordered: fund price drift against the frozen June benchmark, then benchmark-weight changes, then actual portfolio change beyond no-trade drift. The components reconcile exactly. The price-drift component is negligible in this interval; most of the measured Active Share decline comes from benchmark weight changes. The actual fund portfolio differs from the no-trade portfolio by 13.2% one-way, but this is not pure manager turnover or a causal trading estimate.

Yahoo Finance adjusted close via `yfinance 1.8.0` is an exploratory public price source. The package is not affiliated with or endorsed by Yahoo; Yahoo's data terms apply. The 2025 pilot is not pooled with the historical TR/CRSP panel.

## 7. Limitations

- One fund and one three-month interval do not support general conclusions.
- SPY and IWB ETF holdings are proxies for the S&P 500 and Russell 1000, not the index providers' official constituent weights.
- N-PORT reporting and filing dates differ; use `repPdDate` for portfolio timing.
- Yahoo Finance adjusted prices, if used for the next stage, are a public third-party price source and may have ticker history, delisting, corporate-action, and survivorship limitations.
- The 2025 pilot is separate from the 1979–2023 TR/CRSP Active Share panel. Do not pool observations or infer continuity without a validated provider/fund identity bridge.
