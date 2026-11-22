# Findings and Falsification

This page separates validated results from failed predictions, exploratory outputs, and provisional calculations. Read the underlying audit reports before using any result.

## Active Share sample sensitivity

The no-floor fund-count percentile series is not synonymous with active funds. The 5% and 20% Active Share floor series are different samples. Historical S&P 500 asset-weighted slopes were approximately -0.43 percentage points/year for the 5% floor and -0.03 for the 20% floor. Matched-survivor reallocation shifts from approximately -10.44 percentage points to approximately zero. These are not verified active-only results.

The 83% dollar-weighted reallocation claim has not been reproduced on a verified active-only sample and must not be described as such.

## Failed size-gradient prediction

The prediction that larger funds would retreat more decisively did not hold in the prior analysis. This is a negative finding, not a temporary inconvenience. Future work must not quietly reframe or omit it.

## Petajisto identifier bridge

The bridge is viable for a substantial historical subset but incomplete. Ambiguous fund-number/period keys, WFICN disagreements, and separately flagged recoveries remain distinct. See the [match-rate report](https://github.com/tyoungg/market-structure-lab/blob/RUSSEL_SP/research/PETAJISTO_MATCH_RATE_REPORT.md).

## SEC prospectus route

The bounded prospectus work did not produce a usable time-aligned active-only panel. Automated active labels included false positives or ambiguous fund-specific contexts; post-observation evidence cannot be backdated. Unclassified is not passive.

## N-SAR Item 69 — validated extraction

The header audit validated 80/80 sampled CIK processing and found 162/191 target series with at least one header match. This is identity evidence only.

The corrected Item 69 extraction is reproducible in [workflow run 45017599142](https://github.com/tyoungg/market-structure-lab/actions/runs/45017599142), on commit `e236cffa36bbd498cfdeeeccc74f6057531202ed`. The parser now handles both slash-formatted and ISO report dates; all 409 report dates parse, including the 32 ISO-formatted rows that were missed by the original default-inference path. Five parser tests, input validation, extraction, and artifact upload passed. Runtime was 7.35 minutes against a 25-minute deadline.

The validated as-of fund-year panel contains 9 positive Item 69 Y labels, 181 N responses explicitly classified as `NO_NOT_ACTIVE`, and 22,090 unclassified rows. The unclassified rows split into 1,238 without a recent prior N-SAR and 20,852 outside the deterministic 80-CIK sample. The positive labels are three S&P index funds in each of 2007, 2008, and 2009. The evidence output contains 409 series-specific responses covering 117 target series (6 with at least one Y, 111 with N evidence), plus 66 registrant-level rows and 882 unmatched Item 007 mappings. One SEC 504 retrieval error remains recorded.

This is a validated positive index-fund signal for a small, deterministic sample—not an active-only panel. Item 69 N does not prove active management or exclude enhanced-index strategies. The sample is not probability-representative; do not extrapolate.

See the [full N-SAR feasibility and Item 69 audit](https://github.com/tyoungg/market-structure-lab/blob/RUSSEL_SP/research/NSAR_SERIES_LINKAGE_FEASIBILITY.md) and [artifact](https://github.com/tyoungg/market-structure-lab/actions/runs/45017599142/artifacts/14753065280).

## Exploratory simulation

The agent-based model is exploratory and uncalibrated to SPIVA, ICI, CRSP, Notre Dame, or QDIA data. Valuation wedges are model units, not percentage mispricing. The 25% entrant risk cap creates boundary solutions. Mechanism comparisons illustrate a possible channel; they are not empirical proof.

## Required falsification tests
1. Does the manager-choice component disappear after controlling for no-trade drift?
2. Does any enterprise/distribution exposure gradient survive defensible measurement, pre-trends, and controls?
3. Do informed traders or corporate share supply prevent persistent valuation effects after benchmark-driven demand?
4. Are results robust to provider separation, fund attrition, share-class changes, and benchmark definitions?
5. Do negative controls and alternative explanations overturn the result?

Null findings, failed predictions, and attrition belong in the primary report, not only appendices.
