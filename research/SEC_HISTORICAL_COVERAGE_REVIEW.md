# SEC Historical Prospectus Coverage — Results and Manual Review

**Canonical run:** [44966589936](https://github.com/tyoungg/market-structure-lab/actions/runs/44966589936)  
**Artifact:** `bounded-historical-sec-coverage` (14731893436)  
**Code revision:** `a7b9612648b590eb41fe28ccda70ec7c80ce4969`  
**Branch:** `RUSSEL_SP` only

## Executive result

The bounded historical SEC coverage scan completed successfully. The script runtime was 7.57 minutes; the GitHub Actions job ran for approximately 7 minutes 59 seconds. The 70-minute script deadline was not reached. The workflow has a 90-minute job timeout, leaving substantial margin below the project's three-hour ceiling.

The audit covered a deterministic systematic sample of 80 of 551 registrants (191 of 1,262 matched series). It selected 318 filing candidates, of which 78 primary prospectus documents were retrieved and parsed. There were no submission API errors. The 318 candidates comprise 240 accessible submissions with no matched target series ID in the submission header and 78 filings whose primary prospectus document was accessible.

The filing-evidence output contains 131 series-filing rows, representing 117 distinct matched series confirmed in actual submission headers. All 117 confirmed series had an accessible primary document in this pilot. Seventy-one evidence rows contained a candidate strategy context. The automated classifier labeled five series-level rows active and 126 unclassified.

These are sample results, not population estimates. The deterministic registrant sample and severe filing caps are not a probability sample suitable for extrapolating coverage rates to all 551 registrants.

## Manual review of the five automated active labels

The automated active labels are not suitable as C.1 training labels without manual series-identity and time validation.

| Series | Filing date | First/last observed year | Manual assessment |
|---|---:|---:|---|
| Small Cap Growth (S000008810) | 2009-02-02 | 2009 / 2009 | **Reject automated label.** The trigger is the generic phrase “investment manager identifies the securities,” which occurs in boilerplate immediately before a different fund's strategy section. It is not evidence of this series' active stock-selection process. |
| Fidelity Advisor Value Fund (S000017687) | 2009-12-29 | 2008 / 2009 | **Plausible active strategy, post-sample.** Fund-specific text describes FMR's fundamental analysis and selection of companies it believes are undervalued. Filing postdates the final Petajisto observation (2009-09-30). |
| Fidelity Advisor Value Leaders Fund (S000005435) | 2009-12-29 | 2008 / 2009 | **Plausible active strategy, post-sample.** Fund-specific text describes FMR's valuation-based security selection. Filing postdates the final Petajisto observation. |
| Eagle Growth & Income Fund (S000008475) | 2009-02-27 | 2001 / 2008 | **Do not accept without series-level verification.** The extracted context is headed “Capital Appreciation Fund,” not the matched SEC series name. This indicates possible cross-fund context contamination within a multi-fund filing. |
| Dreyfus Structured Midcap Fund (S000000499) | 2009-12-23 | 2004 / 2008 | **Do not label active from this trigger alone.** The extracted text describes a quantitative, risk-controlled, benchmark-aware process. The generic “portfolio managers select stocks” trigger is insufficient to distinguish active from enhanced-index-like implementation. The filing is also post-observation. |

## Time-alignment conclusion

No prospectus-based strategy evidence qualifies for the observed fund-year panel under the conservative rule requiring a filing in a strictly earlier calendar year.

All five automated active labels arise from filings dated in 2009. The Petajisto/TR historical sample ends on 2009-09-30, and the five series' observed windows end no later than 2009. Therefore:
- the two December 29, 2009 Fidelity filings are after the sample;
- the December 23, 2009 Dreyfus filing is after the series' last observed year (2008);
- the February 27, 2009 Eagle filing is after the series' last observed year (2008);
- the February 2, 2009 Small Cap Growth filing is in the same calendar year as its only observed year and is not allowed to classify that year.

The annual coverage table consequently reports zero prior-year strategy-evidence filings. This is the correct conservative outcome, not a missing merge.

## Coverage limitations

- Only 80 of 551 matched registrants and 191 of 1,262 matched series were represented.
- At most one filing per CIK-year and four filings per CIK were selected; the global candidate ceiling was 320.
- 1,010 CIK-years hit the per-year filing cap. The selected filing set is a lower-bound coverage probe, not an exhaustive filing history.
- 240 of 318 candidate submissions did not contain any of the target matched series IDs in the actual submission header. A CIK-level filing is not treated as evidence for every fund under that registrant.
- The series-context extractor can still attach a nearby investment-strategy section to the wrong fund when the primary filing covers multiple funds and the relevant sibling series names are not all represented in the matched target list. This is demonstrated by the Eagle Growth & Income / Capital Appreciation Fund context.
- The automated strategy rules include overly broad triggers (including generic “identifies the securities” and “portfolio managers select stocks”). The five active outputs must not be used as validated active labels.
- The 2010 SEC series/class registry remains a candidate-linkage source, not proof that a series had the same registration identity throughout its observed history.
- The electronic EDGAR archive does not provide a complete pre-1994 filing history; pre-1994 absence is not negative evidence.

## Implications for C.1

1. Do not use the five automated active outputs as ground truth.
2. Do not treat unclassified funds as passive or index.
3. Retain the positive Petajisto index and enhanced-index flags as a separate source of evidence; do not convert missing SEC evidence into a negative label.
4. The current public SEC route does not provide enough time-aligned, series-specific strategy evidence to construct a defensible active-only historical panel across the full 1979–2009 sample.
5. If C.1 requires active-only inference, it needs a separately validated historical classification source or a narrower, explicitly labeled subset with prospectuses dated before the observation periods. This pilot does not justify expanding the SEC scan without first fixing series-context identity and classifier precision.

## Reproducibility

The original machine outputs are preserved in artifact 14731893436:
- `sec_historical_coverage_metrics.json`
- `sec_historical_coverage_by_year.csv`
- `sec_historical_coverage_by_fund_year.csv`
- `sec_historical_coverage_by_series.csv`
- `sec_historical_filing_candidates.csv`
- `sec_historical_series_filing_evidence.csv`
- checkpoint CSVs and submission API error log

No raw source data was committed. Main branch was not modified.
