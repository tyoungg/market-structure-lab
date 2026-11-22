# Prospectus Staleness Sensitivity Protocol

**Workstream:** C.1 — Active-only classification feasibility  
**Branch:** `RUSSEL_SP`  
**Status:** Predeclared sensitivity specification; primary ledger rule remains no universal expiry.

## Question

How sensitive is the usable Tier 1 prospectus-evidence coverage to the age of the latest prior filing at the January 1 fund-year cutoff?

## Primary rule

The primary evidence ledger retains every series-linked prospectus or related filing whose filing date precedes January 1 of the fund-year. No universal expiry is imposed because a prospectus may remain effective for multiple years, may be amended, or may have a separate effective date that is not present in the current extracted artifact. Age is retained as an audit field. A stale filing is not automatically treated as false; it is a reason to inspect amendments/effective dates and report sensitivity.

## Sensitivity windows

Report the following maximum filing ages, measured in calendar days from the fund-year cutoff to the filing date:

| Scenario | Maximum age | Interpretation |
|---|---:|---|
| 1 year | 365 days | Recent annual-document window |
| 2 years | 730 days | Two-year persistence sensitivity |
| 3 years | 1,095 days | More permissive multi-year sensitivity |
| No expiry | None | Primary ledger rule; all prior filings retained |

These are sensitivity bounds, not claims that a prospectus legally expires at these ages. The 365/730/1,095-day cutoffs must not replace the primary no-expiry evidence ledger. Apply the filters after manual strategy adjudication, so the table shows how many already-confirmed active links survive each age cap. Report the number of fund-year/evidence links, unique fund-years, unique evidence events, unique SEC series, and candidate-class counts retained by each window.

## Required safeguards

- Apply the same strict January 1 filing-date cutoff in every scenario.
- Do not use a filing submitted during the fund-year to classify that fund-year.
- Do not backdate later filings or assume a prospectus effective date from its filing date.
- Keep strategy class, identity linkage, and temporal eligibility separate.
- Report both event counts and fund-year link counts; one filing event may support multiple fund-years.
- Item 69 N remains “not reported as index,” not active.
- A staleness window cannot itself convert unclassified evidence into active or passive evidence. Strategy classes are assigned by manual review first; the sensitivity window only includes or excludes those adjudicated evidence links.
- Preserve the no-expiry primary output alongside every sensitivity table.

## Output

The reproducible builder writes `prospectus_staleness_sensitivity.csv` with the four scenarios. All rows are derived only from as-of-eligible Tier 1 evidence events. The table is descriptive coverage sensitivity; it is not a strategy-classification result.

## Decision boundary

If the sensitivity windows materially change evidence coverage, report the effect and inspect whether effective dates or amendments can resolve the cases. Report the active fund-year count retained under each window and show the coverage loss relative to no expiry. A higher evidence-link count improves active-only classification only when the underlying series-specific strategy text has been manually confirmed. C.1 must still retain a no-go outcome if the public record does not support a defensible, sufficiently broad active-only panel.
