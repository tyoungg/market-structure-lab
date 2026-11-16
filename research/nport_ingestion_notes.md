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
