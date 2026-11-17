# N-PORT multi-quarter panel audit — 2026-11-17

## Scope and audit status

This audit uses the published GitHub Actions artifact `nport-eleven-fund-four-quarter-panel` from run 44123116982, plus the compact dashboard outputs on `research/no-trade-large-cap`. It independently re-computes the seven reported Active Share values from the saved ending weights and IVV weights. It does **not** yet independently re-fetch or validate every price observation; the seven estimates remain provisional pending the price/security crosswalk audit below.

## 1. The seven strict intervals

All seven intervals have 100% reported beginning equity-weight return coverage and zero positions missing a return.

| Fund | Interval | Actual end AS vs IVV | No-trade end AS vs IVV | Actual minus no-trade |
|---|---|---:|---:|---:|
| JPMorgan Large Cap Growth | 2025-09-30 to 2025-12-31 | 49.63% | 51.36% | -1.73 pp |
| FMI Large Cap | 2025-12-31 to 2026-03-31 | 94.00% | 93.11% | +0.89 pp |
| JPMorgan Large Cap Growth | 2025-12-31 to 2026-03-31 | 50.77% | 52.04% | -1.28 pp |
| Brown Advisory–Beutel Goodman Large-Cap Value | 2025-12-31 to 2026-03-31 | 95.47% | 96.46% | -0.98 pp |
| FMI Large Cap | 2026-03-31 to 2026-06-30 | 96.51% | 93.91% | +2.60 pp |
| JPMorgan Large Cap Growth | 2026-03-31 to 2026-06-30 | 53.44% | 51.38% | +2.06 pp |
| Brown Advisory–Beutel Goodman Large-Cap Value | 2026-03-31 to 2026-06-30 | 95.13% | 95.34% | -0.20 pp |

### Arithmetic checks passed

- Recomputed all seven actual-end Active Share values from actual end equity weights and same-date IVV weights.
- Recomputed all seven no-trade Active Share values from saved no-trade end weights and same-date IVV weights.
- Recomputed values match stored values to floating-point precision (differences around 1e-14).
- Actual, no-trade, and benchmark equity weights each sum to 1.0 (within floating-point precision).
- No-trade weights are derived from the full starting common-equity sleeve; the seven intervals did not silently drop a starting position.

### What the seven results do and do not say

The seven intervals come from only **three funds**: JPMorgan Large Cap Growth (3), FMI Large Cap (2), and Brown Advisory–Beutel Goodman (2). Four deltas are negative and three positive. The simple mean delta is +0.194 pp; the median is -0.205 pp.

The asset-weighted mean is -0.410 pp, but JPMorgan Large Cap Growth represents approximately 98.7% of the starting net assets across these seven fund-interval observations. The asset-weighted figure is therefore effectively a repeated-observation summary dominated by one very large fund, not a representative estimate across managers. Repeated intervals from the same fund are also not independent observations.

**Interpretation remains descriptive, not causal.** The result is relative to IVV's reported holdings, which are a tracker-fund proxy rather than official S&P 500 weights. Only the common-equity sleeve is modeled; cash, derivatives and other asset classes are outside the modeled sleeve.

## 2. A classification problem in the six "missing observations"

The current panel reports six `MISSING_FUND_OR_BENCHMARK_OBSERVATION` rows: three calendar quarter-end dates for each of two AB funds. This label is misleading. The two funds have fiscal/reporting calendars that do not line up with the hard-coded calendar quarter-end dates.

SEC EDGAR confirms off-calendar N-PORT observations for these same series:

- **AB Large Cap Growth Fund (S000010251):** report dates include 2025-10-31, 2026-01-31 and 2026-04-30. Examples: [2025-10-31 N-PORT](https://www.sec.gov/Archives/edgar/data/889508/000141036825042035/primary_doc.xml), [2026-01-31 N-PORT](https://www.sec.gov/Archives/edgar/data/889508/000141036826032465/primary_doc.xml), [2026-04-30 N-PORT](https://www.sec.gov/Archives/edgar/data/889508/000141036826065271/primary_doc.xml).
- **AB Large Cap Value Fund (S000010411):** report dates include 2025-11-30, 2026-02-28 and 2026-05-31. Examples: [2025-11-30 N-PORT](https://www.sec.gov/Archives/edgar/data/1129870/000141036826006624/primary_doc.xml), [2026-02-28 N-PORT](https://www.sec.gov/Archives/edgar/data/1129870/000141036826040417/primary_doc.xml), [2026-05-31 N-PORT](https://www.sec.gov/Archives/edgar/data/1129870/000141036826074950/primary_doc.xml).

Therefore, the six rows should not be described as proof that those funds had no public observations. The panel's fixed dates simply missed their reporting dates. This is a **date-alignment/design issue**, not yet a data-availability failure.

Before adding these observations, verify whether IVV has a same-date public holdings observation for each date. If not, use a clearly documented same-date public sponsor holdings file or define a consistent alternative benchmark-date rule. Do not silently compare a fund at (say) 2025-10-31 with IVV at 2025-09-30 or 2025-12-31.

## 3. The 20 withheld intervals and security-return coverage

There are 20 intervals withheld for incomplete return coverage. The artifact contains 89 missing-position rows, representing 51 distinct security keys across intervals.

- 81 rows (45 distinct keys) had no usable ticker mapping.
- 8 rows (6 distinct keys) had a ticker selected but no usable Yahoo price series on the required dates.
- Of the 81 no-mapping rows, 16 rows (10 distinct keys) already had a ticker in the N-PORT identifier data. The current return mapper does not use that N-PORT ticker field; it tries ISIN and CUSIP through OpenFIGI, then a separate manual override file.
- OpenFIGI returned no candidate for 71 of the 81 no-mapping rows. Three rows had candidate codes rejected by the ticker-format filter. Seven rows had multiple candidates and the current name-matching logic declined to choose one.

### Examples of remediable public-security mapping gaps

The uncovered list includes public securities such as AvalonBay, Rexford Industrial Realty, Weyerhaeuser, Extra Space Storage, SBA Communications, Equinix and Regal Rexnord. Some have no N-PORT ticker; others have a ticker in the filing that the pipeline currently ignores. These are not necessarily unavailable securities. They are unresolved by the current automated crosswalk.

A concrete selection-logic example is Regal Rexnord: OpenFIGI returned RRX and a when-issued candidate, but the issuer-name comparison did not exactly match the N-PORT description, so the mapper did not select RRX. This is a candidate-review problem, not proof that the security has no price history.

### Private / non-public positions

The missing list also includes private-placement and pre-IPO names such as Canva, Gusto, Stripe, Socure, OpenAI-related securities, Celonis, iCapital, Magic Leap and Chobani. These are not ordinary exchange-traded common stocks with a reliable daily public return series. They should be classified separately (private common, preferred, rights/convertible, etc.) rather than treated as routine ticker-mapping failures.

A defensible public-equity counterfactual may need to report a separately defined **publicly traded common-equity sleeve**, with private/unlisted equity shown as a separate excluded sleeve and its weight disclosed. Do not silently drop it and continue to call the result the full equity sleeve.

## 4. Ticker resolved, but Yahoo supplied no price

The six distinct securities in this group are Sony Financial Group (SFGYY), Kenvue (KVUE), Dayforce (DAY), Comerica (CMA), Interpublic Group (IPG), and Warner Bros. Discovery (WBD). These failures illustrate why a current-ticker price API is not a sufficient historical security master.

Several are confirmed corporate-action / delisting cases:

- **IPG:** Omnicom completed the merger on 2025-11-26. Each IPG common share converted into 0.344 OMC shares, plus cash in lieu of fractional shares. This event occurred *inside* the 2025-09-30 to 2025-12-31 interval. A correct no-trade path must transform the holding into OMC (and any fractional cash), not merely attach a scalar return to an obsolete IPG key. [SEC merger filing](https://www.sec.gov/Archives/edgar/data/29989/000119312525300788/d24786d8k.htm).
- **Dayforce:** the acquisition closed 2026-02-04 for $70 cash per share and the common stock ceased trading. Its missing Yahoo history is consistent with a delisted-symbol coverage limitation, even though the panel interval requiring the return ends 2025-12-31. [SEC-filed acquisition announcement](https://www.sec.gov/Archives/edgar/data/1725057/000114036126003628/ef20064744_ex99-2.htm).
- **Kenvue:** Kimberly-Clark completed the acquisition on 2026-11-02; Kenvue holders received $3.50 cash plus 0.14625 KMB shares per KVUE share, and KVUE ceased trading. The missing history affects earlier panel intervals too. [SEC 8-K](https://www.sec.gov/Archives/edgar/data/55785/000110465926120990/tm2628636d1_8k.htm).
- **Warner Bros. Discovery:** the merger closed 2026-10-06 for $31.01666668 cash per share; WBD ceased trading. Its missing 2026-03-31 to 2026-06-30 price series is a historical-data retrieval problem, because the interval ended before the merger. [Nasdaq corporate-action notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-710).

Comerica also underwent a merger with Fifth Third in 2026, after the interval in which CMA is missing. Sony Financial Group needs separate venue/security validation; do not assume SFGYY is the same tradable line as the N-PORT holding without confirming the instrument.

**Important:** the Yahoo error is not proof that no historical return exists. It can mean that the symbol was later delisted, the feed no longer serves its history, the identifier maps to a non-trading code, or the holding is genuinely unlisted. These cases need different treatments.

## 5. Additional audit limitations in the current pipeline

1. **A 100% coverage flag is not a full validation flag.** It means the code found a ticker and a price on both endpoints. It does not independently prove the ticker is the same security / share class as the N-PORT holding or that all corporate actions were handled correctly.
2. **Raw price levels are not retained in the compact return file.** The artifact stores the computed return, ticker and mapping candidates, but not the adjusted start/end prices used to calculate it. Preserve those levels, price dates, provider, retrieval timestamp and corporate-action fields for reproducibility.
3. **The N-PORT ticker field is not used by the current automatic mapping routine.** It should be a candidate input, followed by issuer/security validation, not accepted blindly.
4. **The manual override file is small and only a partial bridge.** Overrides should carry source URL, effective dates, match rationale and review status.
5. **No explicit corporate-action transformation layer exists.** Merger consideration, stock conversions, cash consideration, spin-offs and delistings can change the security key as well as the value.
6. **The cohort is selected from funds present in the latest 2026 Q3 release and above a June 2026 AUM threshold.** It is size-biased and survivorship-biased. It excludes funds that disappeared before the latest release and can miss historical predecessors / renamed series.
7. **The three largest Q2 2026 security-return outliers (including AMD, WDC and AMAT) should be price-level checked.** They may be genuine large moves; they are flags for independent verification, not presumed errors.

## 6. Recommended sequence before expanding the panel

### Gate 1 — correct the observation calendar
- Build each fund's actual sequence of public N-PORT report dates rather than requiring calendar quarter-end dates.
- Keep intervals within a fund at its actual consecutive report dates.
- Require benchmark holdings at the same ending date; document the source and date if a public sponsor holdings file is needed.
- Replace `MISSING_FUND_OR_BENCHMARK_OBSERVATION` with a more diagnostic status (e.g., no filing in selected archive, report-date mismatch, benchmark-date unavailable, or true series break).

### Gate 2 — build a reviewed security crosswalk
- Use N-PORT ISIN, CUSIP, ticker, issuer name and security description as candidate evidence.
- Use OpenFIGI as a candidate generator, not an unquestioned single source.
- Add SEC/issuer-supported mappings for common public securities; retain effective dates and provenance.
- Explicitly classify public common, ADR, foreign ordinary, ETF/fund, private common, preferred, rights/convertible and unresolved instruments.
- Preserve a manual-review queue for ambiguous candidates.

### Gate 3 — corporate actions and delisted history
- Add an event table that can transform an old security into successor securities and/or cash at the effective date.
- Recover historical prices for later-delisted names from a second public source where available.
- For stock mergers, transform the no-trade holdings into the successor security before calculating ending Active Share.
- For cash acquisitions, specify whether proceeds remain cash in the counterfactual or are reinvested; do not silently keep them in the equity sleeve.

### Gate 4 — reproducibility and independent validation
- Save raw adjusted start/end prices and all price dates for every security return.
- Save the source symbol, permanent identifier, mapping evidence, FIGI candidates, corporate-action treatment and validation status.
- Independently verify a sample of large positions and every material outlier / corporate action.
- Add tests for off-calendar dates, ticker-only N-PORT identifiers, ambiguous FIGI results, delisted securities, stock-for-stock mergers and cash acquisitions.
- Keep the strict full-position rule for the defined modeled sleeve. Report coverage by beginning equity weight and by position count; do not normalize a partial matched subset and label it the whole fund.

### Gate 5 — expand the cohort and history
Only after Gates 1–4 pass, expand beyond the current 11-fund purposive sample. Build the historical cohort from funds observable at each historical date, not only funds still present in the latest release. Include dead, merged and renamed funds when filings permit; retain the fund-series identity and predecessor/successor links. Then extend the panel back through the SEC archive history, rather than extending the current survivor cohort backward.

## Bottom line

The seven calculations pass arithmetic checks, but they are **not yet research-grade estimates**. The largest immediate fix is not adding more funds: it is correcting the fund-specific observation calendar and improving the dated security/corporate-action crosswalk. The six "missing observation" rows are largely a calendar-selection artifact; many of the 20 withheld intervals are held back by fixable public-security mapping or delisted-price gaps, while some private holdings genuinely lack a daily public return. Keep the current results labeled provisional until these issues are addressed.
