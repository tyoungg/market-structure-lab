# Fund-Year SEC Evidence Ledger

**Workstream:** C.1 — Active-only classification feasibility  
**Branch:** `RUSSEL_SP`  
**Issue:** [#11](https://github.com/tyoungg/market-structure-lab/issues/11)  
**Status:** Manual review is recorded in `research/c1_manual_adjudications.csv`; the reproducible builder applies the nine confirmed Item 69 index classifications and preserves the five prospectus dispositions.

## Purpose and unit

The output is a one-row-per-`fundno_key`/year ledger for the Notre Dame/TR–Petajisto historical panel. It keeps SEC identity linkage, filing evidence, temporal eligibility, provisional candidates, and adjudicated classification separate. A companion long table stores each linked fund-year/evidence-event pair. The 2010 SEC series/class registry remains a linkage source, not historical strategy evidence.

## Source artifacts pinned by the workflow

| Source | Workflow run | Artifact | Use |
|---|---:|---|---|
| SEC historical series/filing audit | `44966589936` | `bounded-historical-sec-coverage` | 22,280 fund-years, SEC candidate links, 131 prospectus/filing evidence rows |
| N-SAR header linkage audit | `45013756019` | `historical-nsar-series-linkage` | Series-specific header identity and class IDs |
| Corrected N-SAR Item 69 audit | `45026741058` | `historical-nsar-item69` | Series-level Y/N responses, original six-character coordinates, and precomputed as-of reconciliation panel |

The workflow downloads these frozen run artifacts rather than re-scraping SEC sources. Source SHA-256 hashes are recorded in `fund_year_evidence_ledger_metrics.json`.

## Evidence tiers and temporal rules

- **Tier 1:** prospectus and related filing evidence. Filing date must precede January 1 of the fund-year. Effective-date metadata is not captured systematically in the source artifact; dates visible in primary filings are recorded in the manual register. No universal staleness expiry is invented; age is retained and evaluated under predeclared sensitivity windows.
- **Tier 2:** series-specific N-SAR Item 69 responses. Both filing and report dates must precede the January 1 cutoff, and report age must be 0–548 days. `Y` is a positive index-fund candidate. `N` means not reported as an index fund and is not active evidence.
- **Tier 3:** N-SAR SEC-HEADER series identity matches. These establish historical series identity only, not investment strategy.

Registrant-level Item 69 answers and unmatched Item 007 names are preserved in separate files and never copied to fund-years.

## Initial source reconciliation

The initial local build produced:

| Measure | Result |
|---|---:|
| Fund-year rows | 22,280 |
| Unique fundnos | 2,754 |
| Unique SEC series-linked fund-years | 9,077 |
| Multiple-series ambiguous fund-years | 4,664 |
| No strict SEC candidate fund-years | 8,539 |
| Share-class-ambiguous linked rows | 4,087 |
| Unique linked fund-years in deterministic 80-CIK N-SAR sample | 1,428 |
| Prospectus evidence rows / series | 131 / 117 |
| N-SAR Item 69 evidence rows / series | 409 / 117 |
| N-SAR header identity rows / series | 1,532 / 162 |
| Linked fund-year/evidence-event rows | 17,302 |
| As-of eligible evidence-event links | 855 |
| N-SAR status reconciliation mismatches | 0 |

The 855 as-of eligible evidence-event links comprise 30 prospectus filing-event links, 266 Item 69 response links, and 559 historical header-identity links. These are event links, not 855 distinct fund-years.

The corrected Item 69 panel reconciles exactly to 9 `Y` fund-years, 181 `N` responses (not positive index evidence and still unclassified), 1,238 sampled fund-years without a recent prior N-SAR, and 20,852 rows outside the deterministic N-SAR sample. The last category also contains fund-years for which no unique sampled series linkage is available; it is not a representative coverage rate.

The five automated phrase candidates are manually adjudicated separately: two are plausible active value strategies, one is enhanced-index-like, and two are rejected/unclassified because of series-context mismatch. All five filings are too late or context-invalid to label the observed panel. Direct review of all 30 as-of prospectus fund-year links across 14 series confirms active strategies for all 30 rows.

## Classification boundary

The adjudication promotes 30 fund-years across 14 SEC series to `other_active_style` based on direct review of contemporaneous, as-of prospectus sections. It also promotes nine fund-years (three exact SEC series across 2007–2009) to `passive_index` based on series-specific Item 69 Y responses. The 181 Item 69 N rows remain unclassified and are not active evidence. The remaining 22,241 fund-years remain unclassified. The 30 active rows are only 0.135% of the panel and are clustered in 2007–2009; no representative active-only panel is validated.

The corrected Item 69 artifact retains `item69_coordinate` and `all_item69_coordinates` for all 409 series-level evidence rows. The nine adjudicated fund-years use coordinates `001400`, `002400`, and `004100` across the 2006, 2007, and 2008 filings. The coordinate is preserved from the original response, not reconstructed.

## Outputs

- `fund_year_evidence_ledger.csv` — one row per fund-year.
- `fund_year_evidence_items.csv` — long evidence table with raw response/text, accession, URL, temporal eligibility, and evidence age.
- `series_evidence_inventory.csv` — source inventory by SEC series and evidence tier.
- `fund_year_evidence_annual_coverage.csv` — annual denominators, identity coverage, evidence counts, and final class counts.
- `prospectus_candidate_review_queue.csv` — five automated phrase candidates plus 14 manually reviewed as-of prospectus series, with strategy decisions and panel-eligibility status.
- `c1_manual_adjudications.csv` — reviewer decision register for five automated candidates, 14 as-of prospectus series, 30 prospectus fund-years, and nine Item 69 fund-years.
- `prospectus_staleness_sensitivity.csv` — Tier 1 coverage under 365-, 730-, 1,095-day, and no-expiry scenarios; see [the sensitivity protocol](PROSPECTUS_STALENESS_SENSITIVITY_PROTOCOL.md).
- `nsar_registrant_level_unassigned.csv` — registrant-level answers, not assigned to series.
- `nsar_unmatched_item7_evidence.csv` — 882 unmatched or ambiguous Item 007 mappings.
- `nsar_item69_retrieval_errors.csv` and `nsar_header_api_errors.csv` — source retrieval/processing errors.
- `nsar_item69_coordinate_gap.csv` — only source rows with genuinely missing coordinates; expected to be empty after the corrected extraction.
- `fund_year_evidence_ledger_metrics.json` and `FUND_YEAR_EVIDENCE_LEDGER_AUDIT.md` — machine-readable and human-readable audit summaries.

## Independent audit update

The 30 active prospectus fund-year labels and their 14 series-level source links have now been independently audited; see [C1_ACTIVE30_INDEPENDENT_AUDIT.md](C1_ACTIVE30_INDEPENDENT_AUDIT.md). All 30 active labels were upheld. The full filing-history scan found a later as-of base prospectus within 365 days for every row. This differs from the original selected-source age sensitivity below: the original 13/25/30 counts remain valid for the original selected evidence links, but do not describe the latest available prospectus.

The audit also clarifies that the 23/30 `share_class_ambiguous` flags in this seed set indicate multiple classes within one unique SEC series, not multiple competing portfolio series. A Calvert/Everest predecessor-successor lineage is a candidate for additional recovery and remains outside the adjudicated 30 pending a separate historical-series check.

## Next C.1 work

1. Audit predecessor/successor and historical-series recoveries, starting with Everest/Calvert `fundno 53752`; do not silently backdate the successor series.
2. Assess whether additional contemporaneous prospectus coverage can materially expand the active sample beyond 2007–2009.
3. Preserve the distinction between original selected-source age sensitivity and latest-available prospectus age.
4. Decide whether the public evidence supports any inferential use of an active-only panel; otherwise retain the C.1 no-go for the main historical analysis.


## Canonical reproducibility result

The latest canonical adjudicated build is [run 45028704608](https://github.com/tyoungg/market-structure-lab/actions/runs/45028704608), artifact `fund-year-evidence-ledger` (artifact ID `14757095448`). All eight unit tests passed; the workflow downloaded all pinned source artifacts, applied 30 active prospectus fund-year decisions and nine Item 69 passive-index decisions, validated the accession/as-of guardrails, and uploaded the reproducible output.

The final artifact contains 22,280 fund-year rows: 30 `other_active_style`, nine `passive_index`, and 22,241 `unclassified`. The 30 active rows span 14 series and only 2007–2009. Item 69 coordinates are present in all 409 source evidence rows; N-SAR status reconciliation mismatches are zero. The original selected-source age sensitivity retains 13 active links at 365 days, 25 at 730 days, and 30 at 1,095 days or no expiry. The independent full-history audit found a later as-of base prospectus within 365 days for all 30 active fund-years; see `C1_ACTIVE30_INDEPENDENT_AUDIT.md`. The 30-row active subset remains a manually reviewed seed set, not a representative active-only panel.
