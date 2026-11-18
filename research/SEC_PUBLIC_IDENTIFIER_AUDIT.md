# SEC Public-Data Inventory and Identifier Feasibility Audit

**Branch:** `RUSSEL_SP`  
**Audit date:** 2026-11-18  
**Purpose:** C.1 active-only classification and C.2 modern holdings feasibility  
**Data policy:** Free public sources only. No WRDS, paid vendors, institutional subscriptions, or licensed crosswalks.

## Executive finding

The SEC has substantial public fund-identification and holdings data, but the currently downloaded Notre Dame Active Share panels do not contain a field that directly joins to the SEC fund identifiers.

The Notre Dame TR and CRSP files contain `fundno` / `crsp_portno` and `wficn`. They do **not** contain fund names, tickers, CIKs, SEC series IDs, or SEC class IDs. The SEC Series and Class report contains CIK, series ID, class ID, registrant/series/class names, and class ticker, but no WFICN, TR `fundno`, or CRSP `crsp_portno`.

Therefore, no direct key-based join is available from these files alone. Numeric equality between WFICN and CIK/SEC IDs would be an invalid cross-namespace match and is not attempted. Name/ticker matching requires an additional public source that connects a Notre Dame fund identifier to a contemporaneous name or ticker.

This is a linkage blocker, not evidence that the funds cannot be classified. It must be resolved with a documented public bridge or the affected observations must remain unclassified.

## 1. Public SEC source inventory

| Source | Public coverage shown by SEC | Useful fields / role | Limitation for this project |
|---|---|---|---|
| Investment Company Series and Class Information | January 2010–June 2026 in the latest report | Registrant CIK, series ID, class ID, company/series/class names, class ticker, file number, organization type | No WFICN or Notre Dame fund identifier. SEC notes filer-maintained fields may be inaccurate and the report is not comprehensive for all closed-end funds and UITs. |
| SEC company_tickers_mf.json | Current public crosswalk | Fund CIK, series, class, ticker | No WFICN or Notre Dame fund identifier; no historical ticker/name history guaranteed. |
| Form N-PORT public data sets | October 2019–September 2026 | Registrant CIK, series identifiers, reporting dates, fund and security-level holdings | Modern period only; quarterly publication of publicly disseminated filings; large quarterly ZIPs (hundreds of MB). |
| Form N-CEN public data sets | September 2018–September 2026 | Annual registered-fund, series/class, service-provider and operational information | Modern period only; not a historical 1979–2019 identity crosswalk. SEC currently notes a schema-version coverage caveat. |
| EDGAR submissions API and filing archives | Public filing history / filings; SEC indexes available from 1994 Q3 | Filing CIK, form, filing date, accession and filing path; filings may contain series/class IDs and fund names | CIK identifies the filing registrant, not the Notre Dame fund portfolio. Requires a separate series/portfolio bridge. |
| N-1A, 497, N-CSR and related filings | Public EDGAR filings; series/class IDs required for specified filers from February 2006 | Contemporaneous investment objective, strategy, index language, prospectus and shareholder-report evidence | Filing text is not itself a WFICN crosswalk. Historical coverage and series/class identity must be established per filing. |
| Historical N-SAR filings | Public EDGAR archive where filed | Potential historical registrant/fund evidence | Coverage and linkability to the Notre Dame identifiers remain untested. |

### Official SEC references

- Series and Class Information: https://www.sec.gov/data-research/sec-markets-data/investment-company-series-class-information
- Mutual-fund CIK/series/class/ticker crosswalk: https://www.sec.gov/files/company_tickers_mf.json
- N-PORT data sets: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
- N-CEN data sets: https://www.sec.gov/data-research/sec-markets-data/form-n-cen-data-sets
- EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- Accessing EDGAR data and indexes: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- N-PORT data dictionary/readme: https://www.sec.gov/files/nport_readme.pdf
- N-CEN data dictionary/readme: https://www.sec.gov/files/ncen_readme.pdf

SEC APIs do not require authentication or API keys. Automated requests must identify the application in the User-Agent and comply with SEC fair-access requirements. The SEC publishes bulk submissions JSON nightly. SEC datasets are as-filed/derived data and should be checked against source filings before material classifications are finalized.

## 2. Actual Notre Dame source-file inspection

Source files inspected from the successful public-data workflow artifact (run 44381188999). Raw files remain outside Git.

| Panel | Rows | Distinct primary IDs | Primary ID field | Distinct nonmissing WFICNs | Rows missing WFICN | WFICN row coverage |
|---|---:|---:|---|---:|---:|---:|
| TR, June 1979–December 2019 | 831,289 | 57,980 | `fundno` | 11,677 | 510,844 | 38.55% |
| CRSP, March 2020–September 2023 | 105,334 | 9,083 | `crsp_portno` | 7,076 | 18,712 | 82.24% |

Observed columns relevant to identity:

- TR: `fundno`, `wficn`, `ym`, assets, holdings counts, share-code indicators and Active Share measures.
- CRSP: `crsp_portno`, `wficn`, `ym`, assets, holdings count and Active Share measures.

Neither panel has fund name, ticker, CIK, SEC series ID, or SEC class ID. The panels share WFICN as a field, but that fact alone does not validate a TR-to-CRSP portfolio bridge; provider continuity still requires separate diagnostics.

## 3. Identifier-matching result

| Candidate key | Notre Dame source | SEC public source | Result |
|---|---|---|---|
| WFICN | Present, incompletely populated | Not present in the SEC Series/Class or CIK/series/class/ticker crosswalk fields | No direct join |
| TR `fundno` | Present | Not present | No direct join |
| CRSP `crsp_portno` | Present | Not present | No direct join |
| CIK | Absent | Present | No direct join |
| SEC series ID | Absent | Present | No direct join |
| SEC class ID | Absent | Present | No direct join |
| Ticker | Absent | Present for some classes | Cannot ticker-match without an independent ticker-to-WFICN/name source |
| Fund/series name | Absent | Present | Cannot name-match without an independent name-to-WFICN source |

**Direct public identifier match rate: not computable from the supplied columns; no common identifier exists.** This must not be reported as a zero-percent economic match rate. It is a structural absence of a shared key.

Published research describes matching SEC series IDs to WFICN through fund tickers and then applying one-to-one plausibility checks. The cited implementation uses MFLinks. MFLinks is not a permitted dependency for this project. We may reproduce the *logic* only if a free public source supplies the missing ticker/name-to-WFICN relationship.

## 4. Period feasibility implications

- **1979–2005:** SEC series/class identifiers are not a complete basis for matching the historical TR sample. For specified mutual-fund filers, mandatory series/class identifiers began in February 2006. No comprehensive free historical WFICN-to-name/ticker bridge has yet been identified.
- **2006–2009:** SEC series/class identifiers can appear in relevant filings, but the current SEC Series/Class report begins in 2010. Historical filing-level reconstruction may be possible, but the missing Notre Dame-to-SEC bridge remains.
- **2010–2018:** Annual SEC Series/Class reports are available; N-CEN begins in 2018. These sources improve fund identity and classification evidence only after a portfolio-level bridge is established.
- **2019 onward:** N-PORT adds modern security-level holdings and series identifiers. It can support a separate modern sample after identity linkage and filing-level validation. It does not retroactively solve the historical TR link.

## 5. Next public-only tests

1. Search for a freely accessible, legally reusable WFICN-to-name/ticker crosswalk. Reject sources that are WRDS exports, licensed MFLinks tables, or require institutional access.
2. Test whether public CRSP/Notre Dame documentation, fund sponsor filings, or other openly downloadable records expose a usable mapping. A fund-name similarity without identifier/date corroboration is not a confirmed match.
3. If a public bridge is found, validate time-specific ticker changes, multiple share classes, mergers, one-to-many mappings, and many-to-one collisions. Require contemporaneous evidence and preserve ambiguous cases as unclassified.
4. If no free bridge exists, proceed with an SEC-only modern classification sample only where the SEC series identity can be independently tied to the Active Share observation. Otherwise keep the observation unclassified and report coverage.
5. Keep the 1979–2019 all-fund descriptive baseline separate from any verified active-only sample. Do not project a modern classification backward.

## 6. Acceptance rule

No fund is classified as active or passive from Active Share thresholds, benchmark proximity, ticker/name guesswork, or a non-contemporaneous identity match. A successful match must include source, date, identifier, method, confidence, and reviewable evidence. Unresolved cases remain unclassified.

**Conclusion:** SEC public data is suitable for building a modern fund-identification and classification evidence base, but the current Notre Dame Active Share extracts lack the bridge key needed to join it directly. The next gate is discovery and validation of a free WFICN/name/ticker bridge—not a full N-PORT download.
