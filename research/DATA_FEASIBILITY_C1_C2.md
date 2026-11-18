# Data Feasibility Audit — C.1 and C.2

**Branch:** `RUSSEL_SP`  
**Status:** Initial source feasibility review (web-documented sources; account access not tested)  
**Protocol:** `research/RESEARCH_PROTOCOL.md`

## Executive conclusion

The data pathways for both mandatory benchmarks appear supportable in principle. The key bottleneck is not benchmark identity alone: we must obtain dated fund holdings, security returns, corporate-action/identity continuity, and actual end-period holdings to calculate a no-trade counterfactual. Fund-level licensed data access remains unverified.

No empirical data have been downloaded, linked, or analyzed as part of this audit.

## C.1 Active-only classification

| Requirement | Candidate source | Feasibility/status |
|---|---|---|
| Fund identifiers and fund history | CRSP Mutual Fund Database | Source documented; access not verified |
| Names/style/objectives | CRSP historical fund headers/style/summary | Source documented; access not verified |
| Passive/index classification | CRSP indicators plus contemporaneous fund names, prospectuses, objectives | Requires classification rules and evidence review |
| Share-class and portfolio linkage | CRSP/MFLINKS | Source documented; access not verified |
| Historical Active Share | Notre Dame TR (1979–2019) and CRSP (2020–2023) files | Public data page/source confirmed |
| Fund assets | CRSP total net assets | Source documented; access not verified |
| Survivor/merger/closure history | CRSP | Source documented; access not verified |

**C.1 constraint:** Benchmark proximity or a high Active Share value cannot alone establish a fund's active/passive category. Classification must be evidence-based, contemporaneous, and reviewable. Preserve unclassified observations and quantify them.

Notre Dame's public data page states that TR holdings-based Active Share runs June 1979–December 2019 and CRSP holdings-based data runs March 2020–September 2023, with several benchmark variants including S&P 500 and Russell 1000. These datasets are useful for reproduction/validation but are not a substitute for raw positions needed to construct our own no-trade portfolios.

## C.2 No-trade counterfactual — mandatory parallel benchmark datasets

### S&P 500

| Input | Candidate pathway | Status |
|---|---|---|
| Historical constituent membership | CRSP S&P 500 constituent history through WRDS | Documented |
| Security returns | CRSP daily/monthly stock files | Documented database; account access unverified |
| Historical security identities | CRSP PERMNO and historical linking | Requires validation |
| Benchmark weights | Date-specific constituent market capitalization/validated weights | Requires calculation and validation |
| Fund holdings | TR historical / CRSP | Access unverified |

WRDS documents historical S&P 500 constituent retrieval via CRSP. Membership alone is not benchmark weight. Weight construction must be date-specific, documented, and checked against a trusted benchmark source if available.

### Russell 1000

| Input | Candidate pathway | Status |
|---|---|---|
| Historical constituents | FTSE Russell U.S. index data through WRDS | Documented |
| Historical shares/market values/weights | Monthly Index Holdings US | Documented in university WRDS guides |
| Security returns | CRSP | Documented database; account access unverified |
| Fund holdings | TR historical / CRSP | Access unverified |
| Security identities/corporate actions | CRSP historical security identifiers and corporate-action records | Requires validation |

University research guides describe FTSE/Russell Monthly Index Holdings US with end-of-day constituent holdings, shares, market values, and weights, with history beginning in 1978. This is a promising benchmark source, but our actual licensed access is not confirmed.

**Russell 1000 is a primary analysis, not an appendix or optional robustness check.** It must be built separately using Russell membership and weights, not S&P data.

## C.2 common inputs and methodology blockers

- Dated starting and ending fund positions at a sufficiently comparable interval
- Security total returns over the interval
- Corporate actions, mergers, delistings, spin-offs, splits, and identifier continuity
- Fund-to-portfolio/share-class links and fund style controls
- Cash and non-equity position treatment
- Explicit missing-return/missing-position rules
- Independently testable Active Share calculation
- Sample coverage and unresolved observations disclosed

Ticker alone is not an adequate historical identity key. However, identity-resolution work should remain scoped to the observations needed for this test; it is not the research project by itself.

## Initial source assessment

| Source/data product | Use | Access assessment |
|---|---|---|
| Notre Dame Active Share data | Baseline reproduction and validation | Public source page confirmed |
| CRSP Mutual Fund Database | Fund identities, styles, holdings, returns, assets, survivor history | WRDS product documented; user's access not checked |
| CRSP security files | Returns, historical identifiers, corporate actions | WRDS product documented; user's access not checked |
| CRSP S&P 500 constituent history | S&P membership | Documented through WRDS |
| FTSE Russell Monthly Index Holdings US | Russell 1000 membership/weights/market values | Documented in university WRDS guides; access unverified |

## Source links

- [Notre Dame Active Share data](https://activeshare.nd.edu/data/)
- [Notre Dame Thomson Reuters readme](https://activeshare.nd.edu/assets/473860/tr_active_share_readme.pdf)
- [WRDS CRSP Mutual Funds](https://wrds-www.wharton.upenn.edu/pages/about/data-vendors/center-for-research-in-security-prices-crsp/)
- [WRDS historical S&P 500 constituent retrieval](https://wrds-www.wharton.upenn.edu/pages/grid-items/downloading-the-sp-500-constituents/)
- [Berkeley WRDS guide — Russell Monthly Index Holdings US](https://guides.lib.berkeley.edu/c.php?g=1395730&p=10323507)
- [HBS Library — Russell US Equity Indexes](https://www.library.hbs.edu/databases-cases-and-more/databases/russell-us-equity-indexes)
- [FTSE Russell data subscription](https://www.lseg.com/en/ftse-russell/index-resources/indices-subscribe-data)

## Gate 2 next actions

1. Determine whether we can access WRDS/CRSP and FTSE Russell products through an institutional or personal research account. Do not presume.
2. Confirm availability of the fund holdings files (TR historical and CRSP) for actual start/end position dates.
3. Verify S&P 500 historical constituent data and a defensible dated weight methodology.
4. Verify Russell 1000 monthly constituent holdings/weights and date coverage.
5. Establish a proposed sample period based on overlap of actual available data—not convenience or a desired result.
6. Produce a source/date/coverage matrix with actual evidence (file/table names, fields, sample records) before implementing calculations.

## Known limitations of this audit

This is a source feasibility assessment based on published documentation and web research. It is not a data-access test. Subscription entitlements, schema access, file downloads, completeness, and actual usable observations remain unverified. No empirical results or conclusions are drawn.
