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

## N-SAR Item 69

The header audit validated 80/80 sampled CIK processing and found 162/191 target series with at least one header match. This is identity evidence only.

The initial Item 69 extraction found Y responses for six target series at some point and N responses for 111 target series. A mixed-format date bug affected 32 report dates. Corrected parser code and tests are committed, but the corrected output is pending a fresh workflow run. The locally recalculated 9 Y / 181 N as-of fund-year counts are provisional.

Even after correction, Item 69 does not classify active funds. It may support excluding verified index funds from a sample, while leaving N and unknown records unresolved.

## Exploratory simulation

The agent-based model is exploratory and uncalibrated to SPIVA, ICI, CRSP, Notre Dame, or QDIA data. Valuation wedges are model units, not percentage mispricing. The 25% entrant risk cap creates boundary solutions. Mechanism comparisons illustrate a possible channel; they are not empirical proof.

## Required falsification tests
1. Does the manager-choice component disappear after controlling for no-trade drift?
2. Does any enterprise/distribution exposure gradient survive defensible measurement, pre-trends, and controls?
3. Do informed traders or corporate share supply prevent persistent valuation effects after benchmark-driven demand?
4. Are results robust to provider separation, fund attrition, share-class changes, and benchmark definitions?
5. Do negative controls and alternative explanations overturn the result?

Null findings, failed predictions, and attrition belong in the primary report, not only appendices.
