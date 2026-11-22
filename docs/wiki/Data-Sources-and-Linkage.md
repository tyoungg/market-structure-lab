# Data Sources and Linkage

Raw source datasets are not committed to the repository. This page summarizes public sources and identity-bridge limitations.

## Active Share panels

| Source | Coverage | Role | Limitation |
|---|---|---|---|
| Notre Dame / TR Active Share | 1979–2019; 831,289 fund-quarter observations; 57,980 fund numbers; 163 quarters | Historical baseline | Provider-specific identifiers and definitions; do not pool with CRSP |
| CRSP public extension | 2020Q1–2023Q3; 105,334 observations; 9,083 portfolio numbers | Post-2019 extension | Separate provider; bridge not validated |
| Petajisto Active Share | 81,158 rows; 1980Q1–2009Q3 | Historical ticker/name and identifier bridge | Ticker/name fields are not definitive identifiers |

## Petajisto-to-TR bridge

The audit linked 64,225 unambiguous Petajisto fund-number/period keys to TR. Of these, 63,428 had agreeing WFICNs and 409 were separately flagged recoveries where Petajisto supplied a WFICN missing in TR. There were 388 WFICN disagreements among dual-ID comparisons. The conditional match rate was 79.27% using 81,024 unambiguous keys as denominator. A total of 2,783 of 2,949 distinct Petajisto funds matched at least once.

Recoveries, conflicts, and ambiguous keys remain separate. This is a historical bridge to TR, not an SEC registration bridge and not a basis for extrapolation beyond the Petajisto period.

## SEC registry and prospectus evidence

The SEC 2010 series/class registry is a candidate-linkage snapshot, not proof of historical registration identity. The prospectus pilot did not produce a reliable time-aligned active-only panel. Evidence after the observation period cannot be backdated; generic or ambiguous prospectus language is not sufficient to classify a fund as active.

See [SEC Historical Coverage Review](https://github.com/tyoungg/market-structure-lab/blob/RUSSEL_SP/research/SEC_HISTORICAL_COVERAGE_REVIEW.md) and [SEC Public Identifier Audit](https://github.com/tyoungg/market-structure-lab/blob/RUSSEL_SP/research/SEC_PUBLIC_IDENTIFIER_AUDIT.md).

## N-SAR header identity audit

The bounded header audit processed all 80 sampled CIKs and 1,730 selected filings (at most one per CIK-year). It found at least one header match for 162 of 191 target series (84.82%). The sample is deterministic, not probability-representative. Prior-header coverage begins in 2007; the sample had no prior-header coverage for 1994–2006. Header identity is not strategy classification.

- [Header audit workflow](https://github.com/tyoungg/market-structure-lab/actions/runs/45013756019)
- [N-SAR linkage report](https://github.com/tyoungg/market-structure-lab/blob/RUSSEL_SP/research/NSAR_SERIES_LINKAGE_FEASIBILITY.md)

## N-SAR Item 69 — validated extraction

Item 69 asks whether the registrant/series is an index fund. A series-level Y is positive index-fund evidence. N means only "not reported as an index fund"; it may include enhanced-index or active strategies. Registrant-level answers are not assigned to individual series.

The corrected run processed 282 of 283 selected answer documents and produced 409 series-specific evidence rows covering 117 target series (6 with at least one Y; 111 with N evidence). It retained 66 registrant-level answers and 882 unresolved Item 007 name mappings. One SEC 504 retrieval error is retained in the error output. All 409 report dates parse, including 32 ISO-formatted dates handled by the corrected mixed-format parser.

The joined panel has 22,280 fund-year rows: 9 contemporaneous Item 69 Y labels, 181 N-not-active responses, and 22,090 unclassified. The unclassified group includes 1,238 fund-years without a recent prior N-SAR and 20,852 fund-years outside the deterministic 80-CIK sample. The 9 Y labels represent three S&P index funds in 2007, 2008, and 2009. This is a limited positive index signal, not an active-only classification.

- [Corrected Item 69 workflow](https://github.com/tyoungg/market-structure-lab/actions/runs/45017599142)
- [Corrected Item 69 artifact](https://github.com/tyoungg/market-structure-lab/actions/runs/45017599142/artifacts/14753065280)
- [Parser and regression tests](https://github.com/tyoungg/market-structure-lab/tree/RUSSEL_SP/tests)

## Source boundaries
- EDGAR electronic filings do not cover pre-1994.
- N-SAR was replaced by N-CEN in 2018; do not treat the forms as one unchanged source.
- A missing filing, unmatched name, or absent header is not evidence of active or passive status.
