# N-PORT Phase 0 audit — 2026 Q3 archive

**Audit date:** 2026-11-17  
**Source archive:** SEC 2026q3_nport.zip, supplied in this conversation  
**Purpose:** test whether the public N-PORT data can support the proposed actively managed U.S. large-cap fund no-trade counterfactual.

## Executive result

The Q3 archive is a useful cross-sectional holdings source and supports reliable fund-series/security identification for many common-equity positions. It does **not**, by itself, provide a historical panel for the 2019–2026 study. A full panel requires combining the SEC's separate quarterly archives and resolving amendments across the combined history.

The holdings data also has an important join trap: IDENTIFIERS is one-to-many relative to a holding. Joining it directly to holdings and then summing weights duplicates positions. Identifier rows must be aggregated or handled as a separate bridge.

The no-trade counterfactual is **not yet ready to calculate**. This archive supplies only one public portfolio snapshot for most of the provisional candidate funds, and N-PORT does not supply security-level total returns. Both historical snapshots and a separate security-return source are required.

## 1. Archive scope and filing coverage

The SEC's data page lists quarterly archives from 2019 Q4 through 2026 Q3 and describes the overall dataset as covering October 2019–September 2026. The uploaded Q3 archive is one quarterly release, not a self-contained 2019–2026 panel.

Observed in the uploaded Q3 archive:

| Item | Count |
|---|---:|
| Submission records | 14,066 |
| NPORT-P | 13,938 |
| NPORT-P/A | 128 |
| Holding records | 5,627,083 |
| Identifier records | 6,996,305 |
| Distinct report dates | 13 |
| Earliest report date in this archive | 2024-04-30 |
| Latest report date in this archive | 2026-07-31 |

The report-date distribution is concentrated in May, June, and July 2026. Older dates in this release are sparse and are largely amendment records. Therefore, the 2019–2026 study window requires the separate quarterly releases to be assembled; it cannot be obtained from 2026q3_nport.zip alone.

The SEC describes the data as “as filed,” including amendments, and warns that the extracted data can contain inconsistencies or errors. The original filing remains the validation source.

## 2. Amendment and fund identity findings

- There are 128 NPORT-P/A records in this archive.
- Among records with a populated SERIES_ID, 29 series/report-date groups contain more than one filing.
- Of those 29 groups, 27 contain an original NPORT-P and an NPORT-P/A.
- Two groups contain two same-day NPORT-P submissions for the same series/report date. These are the Founder-Led ETF and Founder-Led 2x Daily ETF records. Their reported holdings and NAV values were identical after excluding filing-specific holding IDs. They should be recorded as duplicate submissions, not treated as separate portfolios.
- 737 of 14,066 records (5.2%) have no SERIES_ID. Of those, 713 have a SERIES_LEI; 24 have neither a SERIES_ID nor a SERIES_LEI.
- A SERIES_LEI alone is not a safe substitute for SERIES_ID: multiple series can share an LEI in this archive. A fallback identity should use at least registrant CIK + series LEI + series name, and records still lacking identity should be quarantined for manual review.
- 24 amendment records have no SERIES_ID, but do have series LEIs. This needs to be handled when the quarterly archives are combined.

**Recommended resolution rule:** concatenate filing metadata across all quarterly archives, deduplicate exact repeated accessions, identify a fund by SERIES_ID where present, and use a clearly flagged composite fallback only where necessary. Within each fund/report-date group, retain the latest valid filing by filing date and accession ordering, while separately auditing same-day duplicate originals and identity fallbacks. Do not treat every accession as a new portfolio observation.

## 3. Identifier join cardinality

The archive contains 6,996,305 identifier rows for 5,627,083 distinct holding IDs.

| Identifier rows per holding | Holding IDs |
|---:|---:|
| 1 | 4,461,587 |
| 2 | 961,770 |
| 3 | 203,726 |

Thus, 1,165,496 holdings (about 20.7%) have multiple identifier rows. A direct one-to-many join from FUND_REPORTED_HOLDING to IDENTIFIERS multiplies some holdings and can materially overstate portfolio weights and holding counts.

**Required implementation:** keep the holdings table at its native accession/holding grain. Build a separate identifier bridge or aggregate identifiers to one row per HOLDING_ID before joining to any portfolio-weight calculation. Preserve all identifiers; do not arbitrarily discard a second identifier. Prefer ISSUER_CUSIP, then ISIN, and use ticker only with additional issuer/security validation.

## 4. Provisional large-cap candidate holdings test

A name-based screen was used only to select a small feasibility sample. These are **provisional candidates**, not a final active-fund universe. N-PORT does not provide a universal active/index flag or a reliable ETF-versus-mutual-fund field; strategy and legal structure must be checked against fund documents.

All positions below are from each selected series' July 31, 2026 filing in this archive. “CUSIP coverage” is the share of reported common-equity weight with a nonblank CUSIP, not the share of rows.

| Provisional fund candidate | Common-equity rows | Unique CUSIPs | Common-equity weight (% NAV) | CUSIP coverage of common-equity weight | All holding weights (% NAV) |
|---|---:|---:|---:|---:|---:|
| Federated Hermes MDT Large Cap Value Fund | 124 | 123 | 97.97 | 100.0% | 99.94 |
| ClearBridge Large Cap Value Fund | 55 | 53 | 99.08 | 100.0% | 99.99 |
| Allspring Large Cap Core Fund | 50 | 50 | 98.13 | 100.0% | 99.86 |
| Madison Large Cap Fund | 30 | 29 | 97.48 | 100.0% | 99.94 |
| Allspring Large Cap Growth Fund | 38 | 35 | 97.44 | 100.0% | 100.07 |
| NYLIM Winslow Large Cap Growth Fund | 51 | 40 | 99.42 | 90.3% | 100.00 |
| Fidelity Blue Chip Growth Fund | 287 | 208 | 98.05 | 92.3% | 100.35 |
| Fidelity Value Fund | 186 | 162 | 99.38 | 90.3% | 102.99 |
| Schwab Large-Cap Growth Fund | 54 | 52 | 99.97 | 100.0% | 100.14 |
| PGIM Quant Solutions Large-Cap Core Fund | 179 | 167 | 98.47 | 100.0% | 99.84 |

The selected common-equity positions have useful CUSIP coverage: 90.3%–100.0% of common-equity weight. Ticker values are much less complete and should not be the primary key. ISIN is available for many positions where CUSIP is absent.

The all-holdings percentage sum is close to 100% for most candidates, but Fidelity Value Fund sums to 102.99% of reported NAV and needs investigation. Fidelity Blue Chip Growth Fund also holds private preferred-equity positions: those positions are not common equity and should not silently disappear from a total-NAV reconciliation.

### Benchmark proxy test

The same archive contains a filing for Schwab S&P 500 Index Fund with 503 common-equity rows, 473 unique CUSIPs, and 99.61% of NAV in common equity. This provides a useful same-date **fund-holdings proxy** for testing CUSIP matching. It is not the official S&P 500 index and must not be described as official index weights. Historical official constituents and weights remain a separate benchmark-data requirement.

## 5. Validation against an original SEC filing

The flattened Q3 archive was checked against the original SEC filing for Fidelity Blue Chip Growth Fund:

- Accession: 0000035402-26-006129
- Report date: 2026-07-31
- Filing date: 2026-09-23
- Series ID: S000007195
- Registrant CIK: 0000754510
- Reported net assets: $98,619,734,675.29

The original filing reports Apple Inc. with CUSIP 037833100, ISIN US0378331005, balance 29,637,243 shares, value $9,155,240,735.13, and 9.283375954390% of net assets. The corresponding flattened holding record matches those values.

The filing lists seven share-class IDs for this series. Portfolio holdings are reported at the series level, while monthly total returns are class-specific. This supports retaining the fund-series as the portfolio unit and not treating each share class as a separate portfolio.

Original filing:
https://www.sec.gov/Archives/edgar/data/754510/000003540226006129/0000035402-26-006129-index.htm

Original filing document:
https://www.sec.gov/Archives/edgar/data/754510/000003540226006129/xslFormNPORT-P_X01/primary_doc.xml

## 6. What N-PORT does and does not provide for the counterfactual

N-PORT provides:
- Series-level holdings and reported percentages of NAV.
- Fund assets, liabilities, and net assets.
- Monthly fund/share-class returns.
- Three-month sales, reinvestment, and redemption flow fields.
- Derivative and securities-lending disclosures in separate tables.

N-PORT does **not** provide security-level total returns for each holding. The no-trade portfolio therefore needs a separate security-return source with corporate actions and delisting treatment. Monthly fund returns cannot substitute for constituent returns.

Flows also need explicit treatment. Series-level sales and redemptions do not identify which securities were bought or sold to meet flows. A pure no-trade weight-drift calculation must state its cash-flow assumption and test sensitivity; it cannot imply that the reported fund flow fields reveal security-level trading.

## 7. Phase 0 status and next work

| Workstream | Status |
|---|---|
| SEC archive ingestion and table schema | Feasible |
| Series/report-date identity and amendment resolution | Feasible with fallback and duplicate audits |
| Security identifier matching | Promising; CUSIP/ISIN preferred, identifier join must avoid fan-out |
| Holdings/NAV quality | Mostly close in the pilot; outliers require audit |
| Active U.S. large-cap fund classification | Not yet validated; prospectus/strategy review required |
| Historical panel 2019–2026 | Not available from Q3 archive alone; all quarterly archives must be assembled |
| Historical S&P 500 weights | Not yet validated; index-fund proxy is not the official index |
| Security-level total returns and delisting treatment | Not yet sourced |
| No-trade counterfactual | Not yet calculated; acceptance tests not passed |

Next sequence:
1. Assemble all quarterly SEC archives from 2019 Q4 onward and resolve filings/amendments across the combined history.
2. Build a fund-series registry with strategy, benchmark, legal structure, and active/index evidence from contemporaneous fund documents. Retain dead, merged, renamed, and liquidated funds where filings exist.
3. Select a security-level total-return source with stable CUSIP/ISIN mapping, distributions, corporate actions, and delisting returns.
4. Re-run the pilot over consecutive public reporting dates; only then calculate no-trade weights and Active Share.

**Conclusion:** N-PORT is a viable holdings source, but the current archive is only a first cross-sectional feasibility test. The historical panel, active-fund classification, official benchmark weights, and security-return source remain prerequisites. No empirical conclusion about active-manager trading versus passive mechanical flows is warranted yet.
