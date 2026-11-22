# Historical Form N-SAR: public identity-linkage feasibility

## Research question

Can contemporaneous SEC Form N-SAR filings provide series/class identity evidence for the historical Petajisto/TR-linked fund panel, improving the time alignment of the SEC series bridge?

## Why this source is worth testing

Form N-SAR was the predecessor to Form N-CEN and was rescinded effective June 1, 2018. SEC EDGAR electronic filing indexes begin in 1994Q3. N-CEN structured datasets begin in September 2018. The public electronic N-SAR window therefore overlaps only part of the 1979–2019 TR history; it cannot solve pre-1994 identity coverage.

The SEC's own filing pages demonstrate that some N-SAR submission headers contain a series/class section with series IDs, series names, class IDs, and class names. A 2008 NSAR-A filing provides a concrete example; its actual header lists multiple series and share classes. A 1994 NSAR-A filing example does not show this section. This makes the header format/date transition a specific empirical question, not an assumption.

## What this source can establish

- A series ID appears in an actual contemporaneous N-SAR submission header.
- The series name and share-class IDs associated with that series in that filing.
- The earliest and latest sampled filing dates at which the target series is confirmed.
- Whether an N-SAR identity record predates a target fund's first observed TR/Petajisto year.

## What it cannot establish by itself

A series/class header is identity evidence, not evidence that the fund is active, passive index, or enhanced index. Registrant-level N-SAR questionnaire responses are not to be treated as fund-specific strategy classifications. Strategy evidence must still come from a fund-specific, contemporaneous prospectus/SAI or another verified source.

## Bounded test design

Reuse the deterministic 80-CIK sample from the prior SEC historical coverage audit, representing 191 target series in the 1,262-series bridge. For each sampled CIK, query the public SEC submissions history and select at most one NSAR-A/B/AT/BT filing per calendar year from 1994 through 2018, preferring NSAR-B. Retrieve only the bounded SEC submission header, not all exhibits. Match actual header series IDs to target SEC series IDs, recording series names and class IDs where present. Use a 43-minute script deadline and 60-minute job timeout. The completed run used 38.11 minutes and did not reach its deadline. No raw source files are committed.

This sample is deterministic and not probability-representative. Results are lower-bound coverage diagnostics and must not be extrapolated to all 551 CIKs.

## Sources

- SEC, Investment Company Reporting Modernization Rules: https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/investment-company-reporting-modernization-rules
- SEC, Accessing EDGAR Data: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- SEC, Form N-CEN Data Sets: https://www.sec.gov/data-research/sec-markets-data/form-n-cen-data-sets
- Example 2008 N-SAR filing header: https://www.sec.gov/Archives/edgar/data/1423227/000123683508000098/0001236835-08-000098.txt
- Example 1994 N-SAR filing: https://www.sec.gov/Archives/edgar/data/917713/000091771394000001/0000917713-94-000001-index.htm

## Acceptance rule

Proceed only if actual header matches are reproducible and improve contemporaneous identity coverage. Do not infer strategy from the presence or absence of N-SAR records. Keep all unconfirmed records unclassified.

## Additional classification field discovered: Item 69

The SEC's official Form N-SAR includes Item 69: “Is the Registrant/Series an index fund?” (Y/N). The form includes a series information block. SEC's own N-SAR answer-key guide explains that answer coordinates distinguish registrant-level responses from series-specific responses; for example, a series-specific coordinate such as `000100` identifies series 01. The answer file also includes Item 007 series ordinals and names, which can be matched to the contemporaneous SEC header's series IDs and names.

This creates a potentially valuable positive index-fund label. The interpretation must remain narrow:
- Item 69 = Y is a direct, contemporaneous positive index-fund response.
- Item 69 = N means only “not reported as an index fund”; it does not establish active management and may include enhanced-index strategies.
- Registrant-level responses are not assigned to every series in a multi-series trust.
- A series-specific answer is mapped only when Item 007's series name uniquely matches a series name in the same filing's SEC header.
- As-of labels require the filing to predate the fund-year and the reported period to be sufficiently recent; same-year evidence is not backdated.

A bounded follow-on extraction is implemented in `scripts/audit_nsar_item69.py`, with parser tests in `tests/test_nsar_item69_parser.py`. It is deliberately separate from the header-only identity audit above. The output will retain YES, NO-not-active, and unclassified as distinct states; it will not create an active-only panel by treating NO as active.

Official sources and examples:
- SEC Form N-SAR, Item 69: https://www.sec.gov/about/forms/formn-sar.pdf
- SEC, Key to Reading N-SAR Document: https://www.sec.gov/info/edgar/forms/nsarkey.htm
- Example series-specific Item 69 values: https://www.sec.gov/Archives/edgar/data/1039803/000100472610000036/answer2.txt
- Example N-SAR Item 69 answer in 2015: https://www.sec.gov/Archives/edgar/data/1039803/000100472615000293/Answer2.txt


## Completed header coverage audit (2026-11-22)

The full deterministic sample completed: all 80 of 80 CIKs were processed, with zero submissions-history request failures and zero CIKs left unprocessed. The run selected 1,730 N-SAR filings (at most one per CIK-year) from 1994–2018.

- Target series in sample: 191 across 80 CIKs.
- Target series found in at least one N-SAR submission header: 162 (84.82%).
- Registrants with at least one N-SAR filing: 79 of 80.
- Registrants with at least one target-series header match: 78 of 80.
- Filing outcomes: 790 target-series matches; 738 headers without series IDs; 131 headers with series IDs but no target match; 71 header retrieval/parse errors.
- Header-name exact matches: 1,241; target-series records with class IDs in the matched headers: 1,532.
- 28 target series had an N-SAR header filed before their first observed year.

The as-of annual table is more restrictive than the ever-matched total. It records no target series with a prior N-SAR header for 1994–2006; prior-header coverage begins in 2007 (130 of 167 observed target series; 77.84%), rises to 141/180 (78.33%) in 2008 and 152/191 (79.58%) in 2009. These are identity-coverage rates, not strategy-label coverage. The full annual table is in `nsar_annual_prior_header_coverage.csv` in the run artifact.

The audit completed in 38.11 minutes against a 43-minute script deadline. The 80-CIK manifest contains 80 completed rows, no history errors, and no unprocessed CIKs. The 71 header errors are filing-level outcomes and remain in the denominator; they are not silently treated as no-match evidence.

This is a deterministic lower-bound sample, not a probability sample. Do not extrapolate its coverage rates to the other 471 registrants or infer that missing header evidence indicates non-index status.

- Completed workflow: https://github.com/tyoungg/market-structure-lab/actions/runs/45013756019
