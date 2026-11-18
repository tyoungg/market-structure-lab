# Public-Data Feasibility Audit — C.1 and C.2

**Branch:** `RUSSEL_SP`  
**Hard constraint:** ONLY freely available public data. No WRDS, paid vendors, subscription databases, or institutional entitlements.  
**Status:** Public-source plan and limitations; access to every proposed public endpoint and full historical coverage must still be tested.  
**Protocol:** `research/RESEARCH_PROTOCOL.md`

## Executive conclusion

The project will use public data only. The user's lack of WRDS access is a settled constraint, not an open question.

The Notre Dame Active Share files already downloaded are the historical descriptive baseline:
- Thomson Reuters (TR): June 1979–December 2019
- CRSP extension: March 2020–September 2023

These files are publicly downloadable and remain usable without a WRDS or CRSP subscription. Their provider labels describe the underlying source data; they do not impose a subscription requirement on this project.

There is, however, an important distinction between reproducing the published Active Share series and independently classifying funds or constructing a security-level no-trade counterfactual. The public Notre Dame files do not, by themselves, provide all the contemporaneous fund documentation, dated positions, security returns, corporate actions, and benchmark weights needed for those additional tests.

**We will not quietly replace missing paid data with invented values, infer fund type from Active Share, or claim a historical active-only result where public evidence is insufficient.** We will quantify public-data coverage and state when a question cannot be answered for a given period.

## 1. Public-data source policy

Allowed:
- Public SEC EDGAR filings and SEC bulk data/API endpoints
- Publicly downloadable Notre Dame Active Share data and documentation
- Public index/ETF holdings files and public benchmark information
- Public security-price and corporate-action data, with source limitations documented
- Public fund prospectuses, statements of additional information, annual/semiannual reports, and other regulatory filings
- Public source code, reproducible downloads, and derived research outputs

Not allowed:
- WRDS or any other subscription database
- CRSP licensed data outside the already-public Notre Dame files
- Bloomberg, FactSet, Morningstar Direct, LSEG/Refinitiv subscriptions, or similar paid products
- Data that is available only through a university license or institutional account

Every dataset added to the project must have a source URL, access date, license/terms review, source-file hash, coverage description, and documented limitations. Raw data should remain in workflow artifacts or external source storage; do not commit large raw files to Git.

## 2. C.1 — Active-only classification

### Public sources to test

| Public source | Potential use | Important limitation |
|---|---|---|
| SEC Form N-PORT filings and SEC N-PORT datasets | Recent fund/series identifiers, portfolio holdings, assets, security identifiers, reporting dates | Coverage begins in the modern N-PORT era; not a 1979–2019 historical classification database |
| SEC Form N-CEN | Registrant, series, class, and fund operational information | Useful for recent identity/series relationships; not a complete historical style classifier |
| SEC Form N-1A and prospectus/SAI filings | Investment objective, principal strategies, index-tracking language, benchmark, mandate | Requires filing retrieval and text/evidence extraction; amendments and dates matter |
| SEC Form 497 filings | Prospectus supplements and strategy/name changes | Filing-level evidence requires dated fund/series matching |
| SEC Form N-SAR historical filings, where available | Older fund/registrant information and historical clues | Coverage, structure, and linkage to the Notre Dame fund identifiers must be tested |
| Notre Dame Active Share files and documentation | Active Share observations, fund identifiers, benchmark measures | Do not assume the files contain all fund names, contemporaneous mandates, or passive indicators |

SEC filing data is public. The project must use SEC's public endpoints and follow its fair-access/rate-limit requirements. We will not depend on paid fund directories or licensed identifier crosswalks.

### Classification method

Classify only when public, contemporaneous evidence supports the assignment. Store the source filing, filing date, series/class identifiers, quoted evidence or extracted text, classification, confidence, and reviewer note.

Required classes:
- Passive index
- Enhanced index
- Active large-cap core
- Other active/style
- Unclassified

Do not use Active Share thresholds or benchmark proximity as a substitute for fund documentation. Keep uncertain cases unclassified.

### Feasibility boundary

A modern public SEC classification can likely be built for a recent N-PORT-era sample, subject to testing the identifier crosswalk between SEC series/class identifiers and the Notre Dame `fundno`/`wficn` or CRSP `crsp_portno`/`wficn` fields.

A comprehensive 1979–2019 historical active-only classification is **not yet demonstrated to be feasible using free public data**. We must test whether public SEC filings and available identifiers support defensible historical matches. If they do not, report the historical all-fund baseline separately and limit active-only conclusions to the period with adequate public evidence. Do not imply that a recent classification can simply be projected backward.

### C.1 outputs

1. Public source inventory and SEC filing download manifest.
2. Identifier crosswalk with match method, confidence, and unresolved cases.
3. Evidence-backed fund classification table with an explicit unclassified category.
4. Annual fund counts, assets, and Active Share distributions by class for periods with adequate coverage.
5. Separate 5% and 20% Active Share floor sensitivities; neither floor defines active status.
6. Missing/unclassified sensitivity and matched-sample/attrition analysis.
7. Clear period-by-period coverage statement, including years where active-only classification is not supportable.

## 3. C.2 — No-trade drift counterfactual

### Public inputs to test

| Input | Public source candidates | Feasibility caveat |
|---|---|---|
| Fund positions | SEC N-PORT filings / public N-PORT datasets | Modern period only; reporting frequency, confidentiality delays, and security coverage must be checked |
| Fund assets and identity | N-PORT, N-CEN, prospectus filings | Need series/class/portfolio mapping and share-class deduplication |
| Security identifiers | CUSIP/ISIN/ticker fields in filings; public issuer/SEC identifiers | Ticker alone is not a stable historical key; some identifiers may be omitted or masked |
| Security returns | Public price-history sources and issuer/corporate-action disclosures | Source quality, adjustment methodology, delistings, and survivorship must be assessed |
| Corporate actions | SEC filings and public exchange/issuer notices; public price-provider adjustment data | Must explicitly handle splits, mergers, spin-offs, delistings, and identifier changes |
| S&P 500 benchmark | Publicly downloadable SPY holdings from State Street as a proxy; public S&P index factsheets/data where available | ETF holdings are not automatically identical to official index constituents/weights; label proxy use |
| Russell 1000 benchmark | Publicly downloadable IWB holdings from iShares as a proxy; public FTSE Russell index information where available | ETF holdings are not automatically identical to official index constituents/weights; label proxy use |

A free ETF holdings file may provide a practical, auditable benchmark-weight proxy for a modern-period experiment. It must not be described as official index history. We must preserve the as-of date, source, holdings, weights, cash, and tracking differences. The S&P 500 and Russell 1000 analyses must be constructed independently.

### Required counterfactual method

For each eligible fund and reporting interval:
1. Validate dated start holdings, positions, weights, identifiers, and cash.
2. Apply security-level returns and supported corporate actions without trading.
3. Re-normalize weights using explicit cash and missing-return rules.
4. Calculate no-trade ending Active Share against the dated benchmark proxy/benchmark.
5. Calculate actual ending Active Share from the subsequent public filing.
6. Compare actual change with mechanical no-trade drift; label the residual as unexplained difference, not manager intent or skill.
7. Report identifier coverage, corporate-action coverage, unmatched holdings, and missing-return exclusions.
8. Run the same procedure independently against S&P 500 and Russell 1000, with compatible style controls and a paired comparison.

### Feasibility boundary

A modern N-PORT-based sample is the most plausible public-only path. It is not equivalent to the 1979–2019 historical TR sample and cannot be used to backfill that history.

Before coding the full counterfactual, test a small, dated sample end to end:
- Obtain two consecutive public N-PORT reports for a set of funds.
- Obtain corresponding public benchmark ETF holdings snapshots for the same dates.
- Resolve security identifiers and public return histories.
- Demonstrate the calculation on hand-checkable funds and dates.
- Quantify missing identifiers, stale holdings, cash, and corporate-action limitations.

If reliable public security-return/corporate-action coverage is insufficient, narrow the counterfactual sample rather than silently substituting data or overstating coverage.

## 4. Provider bridge and sample continuity

TR (1979–2019) and the public CRSP extension (2020–2023) remain separate source panels. No continuous time series is assumed. SEC N-PORT may provide a separate modern validation/sample layer, but it does not itself establish a TR-to-CRSP provider bridge.

## 5. Immediate next steps

1. Build a public-source inventory for SEC N-PORT, N-CEN, N-1A/497, and historical N-SAR, including exact public endpoints, date coverage, schemas, and sample records.
2. Determine whether SEC series/class identifiers can be matched to the Notre Dame fund identifiers using only public evidence. Publish match rates and unresolved counts before classification.
3. Test whether prospectus language supports a reproducible passive/enhanced-index/active taxonomy; preserve unclassified cases.
4. Separately test a small N-PORT no-trade pilot with public SPY and IWB holdings snapshots and public security returns.
5. Continue only with methods whose source coverage and limitations are demonstrable.

## 6. Acceptance rule

A source is eligible only if an ordinary member of the public can access it without a subscription, institutional login, or paid account. A research result is eligible only if its inputs, transformations, exclusions, and limitations can be reproduced from those public sources.

**No WRDS dependency will be introduced.**
