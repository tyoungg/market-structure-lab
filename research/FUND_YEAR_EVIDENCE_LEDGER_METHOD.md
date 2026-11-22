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

- **Tier 1:** prospectus and related filing evidence. Filing date must precede January 1 of the fund-year. Effective dates are absent from the current source artifact and remain a documented limitation. No universal staleness expiry is invented; age is retained and bucketed for later predeclared sensitivity analysis.
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

The corrected Item 69 panel reconciles exactly to 9 `Y` fund-years, 181 `N`-not-active fund-years, 1,238 sampled fund-years without a recent prior N-SAR, and 20,852 rows outside the deterministic N-SAR sample. The last category also contains fund-years for which no unique sampled series linkage is available; it is not a representative coverage rate.

The five automated prospectus candidates are manually adjudicated in `c1_manual_adjudications.csv`: two are plausible active value strategies, one is enhanced-index-like, and two are rejected/unclassified because of series-context mismatch. All five filings are in 2009 and none is eligible under the January 1 information cutoff for the 1980–2009 fund-year panel.

## Classification boundary

The adjudication promotes nine fund-years (three exact SEC series across 2007–2009) to `passive_index`. Their SEC header series IDs/names and Item 007 names agree, and the original Item 69 coordinates contain `Y` in the contemporaneous answer.fil. The 181 Item 69 `N` rows remain unclassified and are not active evidence. The five prospectus candidates have documented strategy dispositions, but none is time-eligible for this panel. The remaining 22,271 fund-years remain unclassified; no active-only panel is created or validated.

The corrected Item 69 artifact retains `item69_coordinate` and `all_item69_coordinates` for all 409 series-level evidence rows. The nine adjudicated fund-years use coordinates `001400`, `002400`, and `004100` across the 2006, 2007, and 2008 filings. The coordinate is preserved from the original response, not reconstructed.

## Outputs

- `fund_year_evidence_ledger.csv` — one row per fund-year.
- `fund_year_evidence_items.csv` — long evidence table with raw response/text, accession, URL, temporal eligibility, and evidence age.
- `series_evidence_inventory.csv` — source inventory by SEC series and evidence tier.
- `fund_year_evidence_annual_coverage.csv` — annual denominators, identity coverage, evidence counts, and final class counts.
- `prospectus_candidate_review_queue.csv` — five automated candidates with manual strategy decisions and panel-eligibility status.
- `c1_manual_adjudications.csv` — reviewer decision register for five prospectus candidates and nine Item 69 fund-years.
- `nsar_registrant_level_unassigned.csv` — registrant-level answers, not assigned to series.
- `nsar_unmatched_item7_evidence.csv` — 882 unmatched or ambiguous Item 007 mappings.
- `nsar_item69_retrieval_errors.csv` and `nsar_header_api_errors.csv` — source retrieval/processing errors.
- `nsar_item69_coordinate_gap.csv` — only source rows with genuinely missing coordinates; expected to be empty after the corrected extraction.
- `fund_year_evidence_ledger_metrics.json` and `FUND_YEAR_EVIDENCE_LEDGER_AUDIT.md` — machine-readable and human-readable audit summaries.

## Next C.1 work

1. Rebuild and independently audit the evidence ledger using the corrected Item 69 artifact and manual adjudication register.
2. Obtain and review effective dates for strategy documents where available; do not backdate filings.
3. Predeclare prospectus staleness windows and run sensitivity tables.
4. Quantify how much of the historical panel remains unclassified under stricter identity and evidence requirements.
5. Decide whether the public evidence supports a valid active-only panel; otherwise document a C.1 no-go.


## Canonical reproducibility result

GitHub Actions run [45027763626](https://github.com/tyoungg/market-structure-lab/actions/runs/45027763626) completed successfully on `RUSSEL_SP`. The workflow downloaded the bounded SEC, N-SAR header, and corrected Item 69 artifacts; all five unit tests passed; the builder applied the manual adjudication register; and the derived bundle uploaded as `fund-year-evidence-ledger` (artifact ID `14756178395`).

The audited output contains 22,280 unique fund-year rows, 17,302 linked evidence-event rows, 855 as-of-eligible evidence links, zero N-SAR reconciliation mismatches, zero missing Item 69 coordinates across the 409 source evidence rows, nine manually adjudicated `passive_index` fund-years, and zero active fund-years. All five prospectus candidates have documented dispositions and none is eligible for the observed panel. The artifact is the canonical reproducible output.
