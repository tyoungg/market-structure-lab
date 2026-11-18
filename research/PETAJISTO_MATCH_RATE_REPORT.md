# Petajisto-to-Notre-Dame TR Match-Rate Report

**Branch:** `RUSSEL_SP`  
**Audit date:** 2026-11-18  
**Workflow run:** [44400738484](https://github.com/tyoungg/market-structure-lab/actions/runs/44400738484)  
**Audited code commit:** `e83c3a6f7416eff0b7fa93bd59b6fc29a1e337b4`  
**Artifact:** `petajisto-public-bridge-audit` (ID `14472329378`, retained through 2026-12-18)  
**Data rule:** Free public data only. Raw source files were downloaded to the runner and were not committed.

## Executive result

**The Petajisto file provides a useful, but not complete, public bridge from its historical fund identifiers to the Notre Dame Thomson Reuters (TR) Active Share panel.**

- Petajisto supplies 81,158 fund-quarter records from **1980-03-31 through 2009-09-30** (not through December 2009 in the downloaded file).
- There are 2,949 distinct nonmissing Petajisto `fundno` values and 2,740 distinct WFICNs.
- 2,783 of 2,949 Petajisto fund numbers match the TR panel at least once: **94.37% distinct-fund coverage**.
- Of 81,091 distinct Petajisto `fundno + reporting-month` keys, 67 are internally ambiguous (the same key has more than one WFICN). Excluding those 67, there are 81,024 unambiguous keys.
- **64,225 unambiguous fundno-period keys match TR: 79.27% of unambiguous Petajisto keys.** If ambiguous keys are retained in the denominator as unresolved, the comparable rate is 64,225 / 81,091 = **79.20%**.
- An independent WFICN + reporting-month join matches 63,638 of 81,158 keys: **78.41%**.
- Of the 64,225 matched fundno-period rows, 63,428 have WFICN agreement between the two sources, 388 have a WFICN disagreement, and 409 have missing TR WFICN. The 388 disagreements are **0.61% of the 63,816 unambiguous dual-ID comparisons** and must be quarantined pending resolution.
- The unambiguous fundno-period match recovers 409 missing TR WFICNs. This is a useful proof of linkage, but it recovers only a small fraction of all missing WFICN rows in the full TR panel.

## Match-rate definitions

The headline denominator is the Petajisto side, because the Petajisto file is the target sample to be linked. A match means an exact equality of normalized identifier and reporting month; no fuzzy name matching is used in these rates.

| Test | Numerator | Denominator | Rate |
|---|---:|---:|---:|
| Distinct Petajisto fund numbers matched at least once | 2,783 | 2,949 | 94.37% |
| Unambiguous Petajisto fundno-period keys matched to TR | 64,225 | 81,024 | 79.27% |
| All distinct Petajisto fundno-period keys, with ambiguous keys unresolved | 64,225 | 81,091 | 79.20% |
| Petajisto WFICN-period keys matched to TR | 63,638 | 81,158 | 78.41% |

The 67 ambiguous fundno-period keys are not accepted as matches. The 388 WFICN disagreements are also not accepted as validated dual-ID links. The remaining 409 rows with missing TR WFICN are candidates supported by a unique fundno-period match; they should remain explicitly tagged as recovered rather than treated as original WFICN observations.

## Annual match rates

Annual rates are calculated over distinct Petajisto fundno-period keys. Ambiguous fundno-period keys remain in the denominator but are not counted as matches. Fund coverage is the percentage of distinct Petajisto fund numbers with at least one unambiguous TR match during that year.

| Year | Petajisto fundno-period keys | Matched keys | Key match rate | Petajisto funds | Funds matched | Fund coverage |
|---:|---:|---:|---:|---:|---:|---:|
| 1980 | 523 | 523 | 100.00% | 160 | 160 | 100.00% |
| 1981 | 578 | 556 | 96.19% | 167 | 167 | 100.00% |
| 1982 | 506 | 438 | 86.56% | 170 | 143 | 84.12% |
| 1983 | 595 | 531 | 89.24% | 188 | 166 | 88.30% |
| 1984 | 668 | 618 | 92.51% | 207 | 186 | 89.86% |
| 1985 | 772 | 717 | 92.88% | 234 | 210 | 89.74% |
| 1986 | 862 | 807 | 93.62% | 263 | 238 | 90.49% |
| 1987 | 945 | 893 | 94.50% | 291 | 269 | 92.44% |
| 1988 | 1,023 | 959 | 93.74% | 310 | 285 | 91.94% |
| 1989 | 1,056 | 968 | 91.67% | 341 | 300 | 87.98% |
| 1990 | 1,226 | 1,114 | 90.86% | 394 | 341 | 86.55% |
| 1991 | 1,347 | 1,205 | 89.46% | 467 | 395 | 84.58% |
| 1992 | 1,263 | 1,122 | 88.84% | 509 | 428 | 84.09% |
| 1993 | 1,799 | 1,532 | 85.16% | 708 | 569 | 80.37% |
| 1994 | 1,886 | 1,358 | 72.00% | 791 | 556 | 70.29% |
| 1995 | 2,064 | 1,401 | 67.88% | 912 | 622 | 68.20% |
| 1996 | 2,401 | 1,823 | 75.93% | 1,009 | 786 | 77.90% |
| 1997 | 2,907 | 2,079 | 71.52% | 1,189 | 908 | 76.37% |
| 1998 | 3,421 | 2,820 | 82.43% | 1,327 | 1,132 | 85.31% |
| 1999 | 3,684 | 3,299 | 89.55% | 1,395 | 1,244 | 89.18% |
| 2000 | 4,292 | 3,906 | 91.01% | 1,530 | 1,355 | 88.56% |
| 2001 | 4,273 | 3,894 | 91.13% | 1,611 | 1,431 | 88.83% |
| 2002 | 4,839 | 4,425 | 91.44% | 1,647 | 1,477 | 89.68% |
| 2003 | 5,195 | 4,514 | 86.89% | 1,717 | 1,513 | 88.12% |
| 2004 | 5,776 | 4,281 | 74.12% | 1,734 | 1,410 | 81.31% |
| 2005 | 6,029 | 4,173 | 69.22% | 1,716 | 1,364 | 79.49% |
| 2006 | 6,150 | 4,071 | 66.20% | 1,673 | 1,227 | 73.34% |
| 2007 | 5,828 | 3,804 | 65.27% | 1,651 | 1,222 | 74.02% |
| 2008 | 5,693 | 3,986 | 70.02% | 1,568 | 1,237 | 78.89% |
| 2009 | 3,490 | 2,408 | 69.00% | 1,384 | 1,088 | 78.61% |

## Data-quality and linkage cautions

1. **Fund-number ambiguity:** 67 Petajisto fundno-period keys map to multiple WFICNs. These are not silently resolved.
2. **WFICN disagreement:** 388 unambiguous fundno-period matches have different nonmissing WFICNs in the two sources. Keep them in a conflict queue; do not choose one ID by convenience.
3. **Missing WFICN recovery:** 409 matched rows have a missing TR WFICN and a nonmissing Petajisto WFICN. Keep a provenance flag distinguishing recovered values from source-provided values.
4. **CSV repair:** 16,388 Petajisto rows contained unquoted commas in the final `fund_name` field. The parser joined overflow fields back into `fund_name` and recorded the repair count and examples. Identifier columns precede the affected field, but the repaired names still need spot-checking before they are used for SEC name matching.
5. **Not an SEC join yet:** This audit links Petajisto to TR. It does not yet prove that ticker/name values map one-to-one to SEC CIK/series/class identifiers. Historical ticker changes, multiple share classes, mergers, and SEC series-level identity still require a separate time-aware test.
6. **Not a full-panel bridge:** This result does not validate the 2010–2019 TR years or the 2020–2023 CRSP extension. Do not carry these matches forward beyond the Petajisto observation dates.
7. **Not an active-only classification:** Petajisto's `indexfund` and `enhanced_index` flags are available in the public file. A missing/zero flag is not, by itself, proof that a fund is active. Use contemporaneous prospectus/filing evidence for classification.

## Reproducibility

- TR archive SHA-256: `5a88154093de361421c53c57dd51c0e3efbf673ba2705f065956b20be893d3f3`
- Petajisto CSV SHA-256: `9ba0fd66fdbdc80798a04cce7e951af93f557ec311315b09d0935fa06cefd8b0`
- The workflow downloads public source data to the runner, computes the join, and uploads derived outputs only. No raw source file is committed.
- Annual CSV and candidate crosswalk are in the 30-day GitHub Actions artifact linked above.

## Conclusion and next gate

The public Petajisto data is a **viable historical bridge candidate** for most of the 1980–2009 TR fund-quarter observations: 94.37% of distinct Petajisto fund IDs match at least once, and 79.20% of distinct fund-quarter keys match when ambiguous keys remain unresolved. However, the 388 WFICN conflicts and 67 ambiguous fund-period keys must be reviewed, and the 16,388 repaired fund names require quality checks.

The next step is to take only the non-conflicting, date-specific Petajisto ticker/name candidates and test them against the SEC Series/Class crosswalk and contemporaneous EDGAR filings. Do not begin active-only historical estimates until that SEC identity and classification bridge is validated.
