# Independent C.1 Audit of the 30 Adjudicated Active Fund-Years

**Scope:** 30 existing `other_active_style` fund-year adjudications, 14 SEC series, nine registrant CIKs.  
**Purpose:** independently test identity, temporal currency, intervening prospectuses, and supplements. This audit does not automatically change strategy classifications.

## Why this audit is required

The earlier SEC historical-coverage scan was a bounded discovery sample: at most one filing per CIK-year and four filings per CIK across the full 1994–2009 period. Its selected prospectus is not necessarily the latest applicable filing for a target series. The old prospectus-age sensitivity therefore measures the age of the selected discovery document, not necessarily the age of the latest available evidence.

## Population and as-of rule

- Input is the 30 rows in `research/c1_manual_adjudications.csv` where `evidence_kind=prospectus_fund_year`, `panel_eligible=true`, and `adjudicated_strategy_class=other_active_style`.
- Expected population: 30 fund-years, 14 distinct SEC series, nine CIKs.
- Each fund-year has a January 1 cutoff.
- A filing dated on or after the cutoff is not eligible for that fund-year.
- The targeted EDGAR history window is 2005-01-01 through 2008-12-31. This covers the filing years capable of superseding the original 2006–2008 evidence used for the 2007–2009 observations.

## Retrieval method

1. Retrieve the SEC submissions history for each of the nine CIKs, including archived submission-history files.
2. Retain all filings in the date window with forms `485APOS`, `485BPOS`, `485BXT`, `N-1A`, `N-1A/A`, `497`, `497K`, `497J`, `497AD`, and `497V`. No per-CIK or per-year filing cap is applied.
3. Parse series identifiers only from the SEC submission header, never from document body text.
4. Retrieve primary documents and attached documents identified as prospectuses, statements of additional information, or supplements.
5. Link documents to target series by SEC header series ID. Where the filing uses a documented name variant, an exact alias list is allowed and retained in the output; fuzzy name matching is not used.
6. Retain filing date, prospectus-date candidates, effective-date candidates, document type, accession, source URL, SHA-256 hash, and a short fund-specific context excerpt.
7. Expand the document inventory to each fund-year only when the filing date is strictly before that year's January 1 cutoff.

## Review rules

- The script creates a candidate-document inventory; it does not decide whether a document supersedes another or whether a strategy changed.
- Review the latest effective base prospectus and every intervening series-specific supplement before accepting a fund-year.
- A later filing may change a sub-adviser, investment universe, objective, or strategy without changing the active/passive class. Record those changes separately.
- A filing-date match does not substitute for checking the stated effective date. Effective-date candidates are retained for manual review.
- Header-only matches are identity candidates, not strategy evidence. A reviewer must confirm that the target series' own strategy section is present.
- Any SEC retrieval error, missing target-series document history, or missing as-of candidate prevents an exhaustive-pass conclusion for the affected series/fund-year.
- The original adjudication remains immutable. Corrections are recorded in a separate independent-audit result.

## Outputs

The workflow artifact `c1-active30-independent-filing-history` contains:

- `c1_active30_document_inventory.csv`: one row per target-series/document link.
- `c1_active30_fund_year_candidates.csv`: documents available before each fund-year cutoff.
- `c1_active30_asof_summary.csv`: per-fund-year inventory summary and original-source comparison.
- `c1_active30_series_coverage.csv`: coverage of all 14 target series.
- `c1_active30_retrieval_errors.csv`: SEC/API/document retrieval errors.
- `c1_active30_audit_metrics.json`: counts, coverage, and retrieval status.

**No original active label is promoted, demoted, or rewritten by this workflow.** The resulting documents must be reviewed before any update to the C.1 ledger or feasibility decision.
