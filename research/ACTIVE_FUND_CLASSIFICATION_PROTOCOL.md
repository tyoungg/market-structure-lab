# C.1 Active-Fund Classification Protocol

**Status:** Operational protocol for the C.1 feasibility gate; no active-only panel is yet validated.  
**Branch:** `RUSSEL_SP`  
**Governing source:** `research/RESEARCH_PROTOCOL.md`  
**Issue:** [#11 — Close the active-only classification feasibility gate](https://github.com/tyoungg/market-structure-lab/issues/11)

## 1. Purpose

Construct a fund-year classification only where contemporaneous, fund/series-specific public evidence supports it. The purpose is to test whether the available public record can support an active-only sample—not to maximize the number of classified observations.

The classification must distinguish:

1. Passive index
2. Enhanced index
3. Active large-cap core
4. Other active/style
5. Unclassified

Unknown is a substantive state. It is not a proxy for active or passive.

## 2. Unit of classification

The target unit is a fund/series-year, not a registrant, ticker, family, or share class by default.

- Link evidence to a contemporaneous SEC series ID wherever possible.
- A registrant-level filing response cannot be copied to every series in a registrant.
- Share classes may be consolidated only after the underlying portfolio/series relationship is verified.
- Keep the source identifier, matched identifier, match method, and ambiguity status in the evidence table.
- If a name match is non-unique, preserve the candidate set and classify the target as unclassified pending resolution.

## 3. Evidence hierarchy

### Tier 1 — Contemporaneous fund/series-specific regulatory strategy documents

Primary evidence:
- Effective prospectus and statement of additional information (N-1A, 497, and related amendments).
- Fund/series-specific statements in annual or semiannual reports when they directly describe the mandate.
- Explicit strategy and objective language attributable to the identified series.

For each evidence item retain filing accession, filing date, effective date when available, series/class mapping, source URL, extracted passage, extraction method, and reviewer decision.

### Tier 2 — Contemporaneous series-level regulatory questionnaire evidence

SEC Form N-SAR Item 69 asks whether the registrant/series is an index fund.

- A series-specific **Y** is positive index-fund evidence.
- A series-specific **N** means only “not reported as an index fund.” It is not evidence of active management and may include enhanced-index strategies.
- Registrant-level answers are not assigned to series.
- An answer is mapped only when the Item 007 series name uniquely matches the series name in the same filing header.
- Preserve the original coordinate, scope, answer, accession, filing date, and report date.

The corrected extraction found 9 as-of Y fund-years and 181 N-not-active fund-years in the deterministic 80-CIK sample. These figures are not an active-only classification.

### Tier 3 — Supporting identity and context evidence

SEC series/class registries, contemporaneous fund names, ticker histories, benchmark references, and other filing metadata can support identity resolution or guide document retrieval. They do not independently establish strategy.

A name containing “Index,” a ticker match, a benchmark name, or a high/low Active Share value is not sufficient by itself to assign a strategy class.

## 4. Class-specific positive evidence rules

### Passive index

Require affirmative evidence that the series seeks to track, replicate, or substantially match a named index, or an equivalent explicit index-tracking mandate. A series-level N-SAR Item 69 Y is a strong positive index-fund flag; retain it as a distinct source field and review the contemporaneous strategy document where available for conflicts or evidence of a materially different mandate.

Do not infer passive status from low Active Share, benchmark proximity, low turnover, or the word “index” in a name alone.

### Enhanced index

Require explicit contemporaneous language describing an enhanced-index, index-plus, enhanced indexing, or comparable mandate that seeks to outperform or improve on an index while remaining index-oriented. Do not classify a fund as enhanced index merely because it answers N to Item 69, has modest Active Share, or uses an index as a benchmark.

### Active large-cap core

Require both:
1. Positive evidence of discretionary active portfolio management or security selection rather than an index-tracking/enhanced-index mandate; and
2. Positive evidence that the mandate is large-cap core, not merely a large-cap growth, value, sector, or other style mandate.

A fund's Item 69 N answer is not sufficient. Nor is the absence of an index-tracking statement in an incomplete filing.

### Other active/style

Require positive evidence of discretionary active management, but the mandate is a style, sector, thematic, international, small/mid-cap, or other category outside active large-cap core.

### Unclassified

Use when evidence is missing, stale/temporally invalid, ambiguous, contradictory, not series-specific, or insufficient to distinguish index, enhanced index, and active. Record the specific reason; do not silently drop these rows.

## 5. As-of timing

The primary annual panel uses a January 1 information cutoff for each observation year unless the governing analysis pre-registers another cutoff.

- Filing date must be before the cutoff.
- Effective date, if available, must also be before the cutoff.
- A document filed or effective after the cutoff cannot classify that year's observation.
- Report period and filing date must both precede the cutoff for N-SAR questionnaire evidence.
- The current N-SAR extraction uses a 548-day maximum age for the reported period. Retain that rule explicitly; do not silently change it.
- For prospectus/SAI evidence, preserve document effective date, filing date, supersession/amendment links, and age. The acceptable staleness window must be predeclared and sensitivity-tested before producing the primary panel; this protocol does not invent a universal expiration period.
- Where multiple valid documents exist, use the latest effective evidence before the cutoff, but retain earlier and conflicting evidence in the audit trail.

Do not backdate later filings, later strategy language, or current fund descriptions.

## 6. Conflicts and adjudication

- If Tier 1 strategy evidence conflicts with a questionnaire flag, retain both and mark the case for manual review; do not automatically overwrite either source.
- If two contemporaneous documents conflict, inspect effective dates, amendments, series identity, and whether the strategy changed.
- If the conflict cannot be resolved from public evidence, classify as unclassified with reason `conflicting_evidence`.
- A reviewer must record the quoted passage, decision, rationale, and date. A second reviewer or independent audit should examine all positive active labels and a reproducible sample of borderline cases before the panel is called validated.

## 7. Required evidence-table schema

At minimum, retain these fields per evidence item:

| Field | Description |
|---|---|
| `fundno`, `wficn`, `crsp_portno` | Available research-side identifiers |
| `cik`, `series_id`, `class_id` | SEC identifiers |
| `fund_year` | Target observation year |
| `filing_accession`, `source_url` | Exact public source |
| `filing_date`, `effective_date`, `report_date` | Timing fields |
| `source_tier`, `source_type` | Evidence hierarchy |
| `quoted_evidence` | Short supporting passage or structured response |
| `candidate_class`, `final_class` | Proposed and adjudicated class |
| `match_method`, `match_confidence` | Identity linkage |
| `evidence_age_days` | Age at the as-of cutoff |
| `review_status`, `reviewer_note` | Human review and rationale |
| `unclassified_reason` | Explicit reason where unresolved |

Store evidence rows separately from the fund-year classification table. Never overwrite source facts with reviewer conclusions.

## 8. Required diagnostics and acceptance criteria

Report by year and source:
- Total fund-year denominator and unique funds/series.
- Counts and assets in each of the five classes.
- Unique, ambiguous, unmatched, and unresolved identity links.
- Evidence coverage, stale evidence, filing retrieval failures, and missing documents.
- Conflicts and manual-review outcomes, including false-positive rate among reviewed positives.
- Results under predeclared alternative staleness windows and identity-link restrictions.
- Attrition from the original TR/CRSP panels to the evidence-backed sample.
- Separate results for the deterministic SEC 80-CIK sample and the full research panel; never extrapolate the sample's classification rate to unsampled funds.

C.1 passes only if positive active classifications are supported by contemporaneous series-specific evidence, false positives are acceptably low under documented review, and the annual denominator/attrition is transparent. If the public evidence cannot support this, record a no-go result and retain the all-fund descriptive series as a different estimand.

## 9. Current evidence boundary

- Petajisto-to-TR provides a substantial but incomplete historical identifier bridge; it is not an SEC strategy classification.
- The SEC 2010 registry is a candidate-linkage snapshot, not proof of historical registration identity.
- The bounded prospectus route did not produce a reliable time-aligned active-only panel.
- The N-SAR header audit found 162/191 sampled target series in at least one sampled header; annual prior-header coverage begins in 2007. This is identity coverage, not strategy coverage.
- Corrected N-SAR Item 69 extraction: 9 Y fund-years, 181 N-not-active fund-years, 22,090 unclassified fund-years; deterministic 80-CIK sample, one filing-level 504 error retained. See [the full audit report](NSAR_SERIES_LINKAGE_FEASIBILITY.md) and [workflow run 45017599142](https://github.com/tyoungg/market-structure-lab/actions/runs/45017599142).

No active-only panel is currently validated. The next step under issue #11 is to build and audit the evidence-level fund-year ledger, beginning with the existing SEC series links and filings, and make an explicit go/no-go decision.
