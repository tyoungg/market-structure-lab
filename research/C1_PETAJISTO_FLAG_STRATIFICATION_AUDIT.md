# C.1 — Petajisto Positive-Flag Stratification Audit

**Branch:** RUSSEL_SP  
**Status:** Reproducible source-aware stratification; **not** a validated active-only classification.  
**Provider:** Thomson Reuters (TR) only. CRSP is not pooled or analyzed in this step.

## Executive result

The validated public Petajisto-to-TR crosswalk supports a limited, source-attributed split of the historical TR panel. It does **not** support relabeling the residual observations as active funds.

| Measure | Result |
|---|---:|
| TR fund-quarter rows, 1980–2009 | 388,913 |
| TR unique funds, 1980–2009 | 33,836 |
| Eligible linked fund-quarter rows | 63,837 |
| Linked-row coverage of TR window | 16.41% |
| Unique linked TR funds | 2,754 (8.14% of TR funds in window) |
| Primary WFICN agreements | 63,428 |
| Separate recoveries with missing TR WFICN | 409 |
| WFICN disagreements excluded | 388 |
| Petajisto pure-index positive flags | 3,551 (5.56% of linked rows) |
| Petajisto enhanced-index positive flags | 429 (0.67%) |
| Neither positive flag — **unclassified** | 59,857 (93.77%) |

The upstream crosswalk also excluded 67 ambiguous fundno/period keys. The 409 recoveries remain a separately identified linkage class; they are not silently combined with the primary identifier-agreement records.

## What the flags mean — and do not mean

Petajisto's published variable definitions identify indexfund as an indicator for a pure index fund and enhanced_index as an indicator for an enhanced-index fund. These are positive source labels. A zero in either field does **not** establish that a fund is actively managed. The 59,857 linked records with neither positive flag therefore remain unclassified.

A second distinction matters for this project: the TR as_s5 and as_r1 fields measure Active Share against the S&P 500 and Russell 1000. Petajisto's indexfund flag refers to a fund classified as a pure index fund using its own official benchmark. A fund tracking a different index can consequently have high Active Share against the S&P 500 or Russell 1000 while still being a pure index fund. These positive flags must not be interpreted as “low Active Share against either of our two study benchmarks.”

No fund is classified as active from a zero flag, a high Active Share value, or benchmark proximity. No SEC-derived strategy labels are carried forward: the prior SEC filing audit did not produce usable prior-period strategy evidence.

## Method

1. Rebuild the public Petajisto-to-TR crosswalk from the public Notre Dame TR archive and Petajisto ASCII file.
2. Retain unique fundno/period keys with agreeing nonmissing WFICNs as primary_wficn_agreement.
3. Retain unique keys where TR WFICN is missing but Petajisto supplies one as recovered_missing_tr_wficn.
4. Exclude WFICN disagreements; do not include the upstream ambiguous fundno-period keys.
5. Join the resulting 63,837 records to TR on fundno and month.
6. Assign only the two positive Petajisto flags. All other linked records remain unclassified; unmatched TR rows receive no classification.
7. Calculate annual fund-quarter distributions separately for S&P 500 and Russell 1000 Active Share. Asset-weighted means use contemporaneous TR total assets; asset sums in outputs are sums over fund-quarter observations, not unique AUM.
8. Recalculate the distributions in three separate samples: no floor (AS >= 0%), 5% floor, and 20% floor. The floors are sample sensitivities, not strategy definitions.

## Floor sensitivity

Counts below are fund-quarter observations in the linked sample, summed over 1980–2009. The filters are benchmark-specific.

| Benchmark | Floor | Pure-index flag | Enhanced-index flag | Unclassified |
|---|---:|---:|---:|---:|
| S&P 500 | 0% | 3,551 | 429 | 59,857 |
| S&P 500 | 5% | 2,177 | 390 | 59,857 |
| S&P 500 | 20% | 1,782 | 355 | 59,823 |
| Russell 1000 | 0% | 3,551 | 429 | 59,857 |
| Russell 1000 | 5% | 3,549 | 429 | 59,857 |
| Russell 1000 | 20% | 1,716 | 348 | 59,848 |

The floors materially change the number of observations carrying positive index flags, especially for S&P 500 Active Share. They barely change the unclassified sample. That is a sensitivity result, not evidence that the residual sample is active-only.

## Descriptive annual series — interpretation boundary

The annual output includes counts, medians, percentiles, equal-weighted means, and asset-weighted means by source class and link type. For illustration, in the primary-agreement, no-positive-flag subset, the S&P 500 asset-weighted mean is 82.56% in 1980 and 72.59% in 2009; the Russell 1000 figures are 83.80% and 73.92%. These are **not active-only estimates**. They describe the unclassified linked subset, which covers only 16.41% of TR fund-quarter rows and 8.14% of TR funds in the Petajisto window. Do not extrapolate them to the full TR panel or use them to validate the 83% active-only reallocation claim.

The Petajisto flags end in 2009. They are not projected onto TR observations outside 1980–2009 or onto CRSP 2020–2023.

## Outputs

- c1_annual_flag_stratification.csv — annual fund-quarter distributions by positive source flag/unclassified group, link type, and benchmark.
- c1_annual_flag_floor_sensitivity.csv — separate 0%, 5%, and 20% benchmark-specific floor samples.
- c1_annual_match_coverage.csv — annual linked-row coverage relative to all TR observations.
- c1_classification_counts.csv — row, distinct-fund, and fund-quarter asset totals by source class and link type.
- c1_petajisto_flag_matched_panel.csv — joined row-level panel for audit.
- c1_flag_stratification_metrics.json — machine-readable scope and validation metrics.

## Conclusion / next gate

This work improves C.1 by isolating source-confirmed pure-index and enhanced-index observations and by quantifying how much of the historical TR universe remains outside the classification bridge. It does **not** pass the protocol's active-only classification gate. The defensible result is a positive-label stratification plus a large unclassified remainder. A full active-only historical panel remains unsupported by the public evidence assembled so far.

The next useful C.1 step is to test whether additional public contemporaneous evidence can improve classification coverage without turning zero flags into active labels. Until then, report all-fund baseline, positive index flags, positive enhanced-index flags, and unclassified observations separately.

## Sources

- Petajisto public Active Share data page: https://www.petajisto.net/data.html
- Petajisto (2013) data-variable definitions: https://www.petajisto.net/data/activeshare.pdf
- University of Notre Dame Active Share data: https://activeshare.nd.edu/data/
