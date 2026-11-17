# N-PORT ingestion: first-pass inspection

## Source

The pipeline uses the SEC's official quarterly Form N-PORT data-set archives:

https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets

The SEC readme documents up to 30 tab-delimited UTF-8 tables plus a metadata file. The data is "as filed" and includes amendments. The SEC cautions that the flattened data may contain errors and is not a substitute for the original filing.

## First inspection

The SEC 2026 Q3 archive is listed at approximately 441 MB. Download only when ready; it is not committed to Git.

On macOS/Linux:

```bash
export SEC_USER_AGENT="MarketStructureLab research contact your-real-email@example.com"
python scripts/inspect_nport.py --quarter 2026q3 --download --count-rows
```

Or use an archive already downloaded:

```bash
python scripts/inspect_nport.py --quarter 2026q3 --archive /path/to/2026q3_nport.zip --count-rows
```

The script extracts the six core tables to `data/nport/2026q3/`:
- `SUBMISSION.tsv`
- `REGISTRANT.tsv`
- `FUND_REPORTED_INFO.tsv`
- `FUND_REPORTED_HOLDING.tsv`
- `IDENTIFIERS.tsv`
- `FUND_VAR_INFO.tsv`
- `manifest.json` records source, table member names, columns, file sizes, and optional row counts.

To extract all tabular tables, add `--all-tables`.

## First-pass schema map

| Table | Grain / key | Use |
|---|---|---|
| SUBMISSION | One row per `ACCESSION_NUMBER` | Filing date, form type, report date, report ending period |
| REGISTRANT | One row per `ACCESSION_NUMBER` | Registrant CIK, name, file number, LEI |
| FUND_REPORTED_INFO | One row per `ACCESSION_NUMBER` | Series name/ID/LEI, total assets, liabilities, net assets |
| FUND_REPORTED_HOLDING | One row per `ACCESSION_NUMBER` + `HOLDING_ID` | Issuer, CUSIP, balance, units, currency value, percentage of fund NAV, payoff profile, asset category |
| IDENTIFIERS | One row per `HOLDING_ID` + `IDENTIFIERS_ID` | ISIN, ticker, other identifiers |
| FUND_VAR_INFO | One row per `ACCESSION_NUMBER` | Designated index fields, only relevant to funds subject to relative VaR test |

The intended joins are:
- `SUBMISSION`, `REGISTRANT`, `FUND_REPORTED_INFO`, and `FUND_VAR_INFO` on `ACCESSION_NUMBER`.
- `FUND_REPORTED_HOLDING` to filing-level tables on `ACCESSION_NUMBER`.
- `IDENTIFIERS` to holdings on `HOLDING_ID`.

The SEC schema documents `HOLDING_ID` as the key for each holding and `IDENTIFIERS_ID` as the secondary key. We will validate uniqueness and join cardinality empirically on the archive before relying on these relationships.

## Important interpretation cautions

1. **Quarterly public snapshots:** N-PORT filings concern monthly holdings, but the public SEC dataset includes only information from filings that have been disseminated. Do not assume every monthly portfolio is publicly available.
2. **Amendments:** the dataset includes NPORT-P and NPORT-P/A records. Do not append them as independent portfolio observations. The next phase must define a deterministic "latest valid filing per series and report date" rule and audit amended records.
3. **Fund identity:** registrant CIK is not the fund-series identifier. Preserve `SERIES_ID` and `SERIES_NAME` alongside registrant identity.
4. **Security identity:** do not rely on ticker alone. Retain CUSIP, ISIN, LEI, ticker, issuer name, issue title, and source filing identifiers wherever available.
5. **Asset categories:** do not assume all holdings are common stocks. Preserve `ASSET_CAT`, `ISSUER_TYPE`, and `PAYOFF_PROFILE`; define a security inclusion map only after inspecting observed values and the SEC definitions.
6. **NAV percentages:** `PERCENTAGE` is reported relative to fund net assets. Preserve the reported value and test how it reconciles to reported NAV. Do not silently renormalize an equity-only subset to 100%.
7. **Benchmark:** `DESIGNATED_INDEX_NAME` is not a universal fund benchmark. It is a relative VaR field and may be missing for many funds.
8. **Data quality:** validate selected rows against original EDGAR filings. Preserve amendments, accession numbers, raw tables, and extraction manifests.

## Dependencies

The inspection script uses Python's standard library and pandas, which is already in this repository's requirements.

## Scope of this script

This is an ingestion/inspection utility only. It deliberately does not classify funds, resolve amendments, select funds based on current survival, classify equity instruments, map security identifiers across time, download security returns, or calculate no-trade portfolios or Active Share. Those steps require explicit methods and separate tests.


## 2026 Q3 archive audit — important implementation corrections

A full inspection of the uploaded 2026 Q3 archive is documented in [nport_phase0_q3_audit.md](nport_phase0_q3_audit.md).

Two important corrections for future processing:

1. **Quarterly archive assembly:** the SEC's 2019 Q4–2026 Q3 coverage is spread across separate quarterly releases. The 2026 Q3 ZIP alone contains 14,066 submission records and only 13 report dates (2024-04-30 through 2026-07-31), concentrated in May–July 2026. Do not treat one quarterly ZIP as the full historical panel. Combine the quarterly archives before building the 2019–2026 time series.
2. **Identifier join fan-out:** the Q3 archive has 6,996,305 identifier rows for 5,627,083 unique holding IDs. About 20.7% of holdings have multiple identifier rows. A direct join from holdings to identifiers multiplies positions. Aggregate or bridge identifiers at the holding level before calculating weights; preserve multiple identifiers rather than dropping them.

Additional identity checks:
- 737 submissions lack SERIES_ID; 713 of these have SERIES_LEI, and 24 have neither. SERIES_LEI is not unique enough to use alone. Use SERIES_ID where available and a flagged composite fallback (registrant CIK + series LEI + series name) otherwise.
- The archive has 128 amendments. Resolve amendments across the combined archive history, not within one quarter only.
- A sample Fidelity Blue Chip Growth Fund filing was matched to the original SEC filing, including series ID, NAV, Apple CUSIP/ISIN, shares, value, and NAV percentage.


## Security-return source research

CRSP via WRDS is the strongest institutional candidate identified so far for security-level monthly total returns, historical security identifiers, corporate actions, and delisting treatment. CRSP also provides historical S&P 500 membership through WRDS. However, CRSP is subscription data, and index membership is not the same as official float-adjusted index weights. UF Libraries lists CRSP stock data and the survivor-bias-free U.S. mutual-fund database via WRDS; project access has not been confirmed.

References:
- https://www.crsp.org/research/crsp-us-stock-databases/
- https://www.crsp.org/crsp_pdf/crsp-us-stock-indexes-databases-data-descriptions-guide-crspaccess/
- https://wrds-www.wharton.upenn.edu/pages/classroom/the-sp-500/
- https://businesslibrary.uflib.ufl.edu/az.php

This creates a scope decision for later: CRSP is the better research-quality return source if institutional access is available and subscription data is acceptable. If the project must remain fully public-data-only, the return source and delisting treatment need a separate feasibility test.


## Filing resolver rule added in the pilot pipeline

The pilot resolver treats only `NPORT-P` and `NPORT-P/A` as portfolio observations. `NT NPORT-P` is a notice of late filing, not a holdings snapshot, and is excluded from the resolved panel. Within each fund-series/report-date group, the latest valid filing date wins; `NPORT-P/A` has priority over `NPORT-P` on a same-day tie, followed by accession ordering as a deterministic final tie-breaker. The resolver retains the full filing rows and a group filing count for audit.

This rule is implemented in `scripts/run_nport_pilot.py` and covered by a synthetic unit test. It must be applied after concatenating all quarterly archives and deduplicating repeated accessions when the full historical panel is built.
