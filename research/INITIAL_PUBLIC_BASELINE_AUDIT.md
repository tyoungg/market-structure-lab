# Public Active Share Dataset — Initial Baseline Audit

**Branch:** `RUSSEL_SP`  
**Data source:** University of Notre Dame public Active Share dataset, user-provided downloads  
**Status:** Raw-data load and first descriptive audit complete. This is not an active-only analysis.

## Source files and periods

- Thomson Reuters (TR): June 1979–December 2019; 831,289 observations; 57,980 unique `fundno` values; 163 distinct quarterly dates.
- CRSP: March 2020–September 2023; 105,334 observations; 9,083 unique `crsp_portno` values; 15 distinct quarterly dates.

The periods are kept separate because they use different holdings-data providers. No continuous TR-to-CRSP series is assumed.

## Benchmark fields verified

- `as_r1`: Russell 1000
- `as_s5`: S&P 500

Benchmark code mapping is documented in the Thomson Reuters readme. Active Share observations in the public files are all-fund observations and are not an active-only classified sample.

## Raw all-observation descriptive statistics

| Source | Observations | Fund IDs | Russell 1000 mean | Russell 1000 median | Russell 1000 asset-weighted | S&P 500 mean | S&P 500 median | S&P 500 asset-weighted |
|---|---:|---:|---:|---:|---:|---:|---:|
| TR | 831,289 | 57,980 | 89.43% | 96.62% | 67.08% | 88.67% | 96.66% | 65.78% |
| CRSP | 105,334 | 9,083 | 87.25% | 97.76% | 56.23% | 86.76% | 98.16% | 55.00% |

Asset-weighted figures weight each fund-quarter observation by `total_assets`. These are descriptive statistics only; they are not yet a fund-style classification or a time-series inference.

## Data integrity checks

- Date fields parsed successfully for all records.
- No missing values in the two target benchmark Active Share fields in either file.
- No duplicate fund-quarter keys detected in the initial audit.
- No missing dates.
- TR target Active Share fields are within [0, 1].
- CRSP has five tiny negative values in `as_s5` (approximately -1e-8 to -4e-8) and one tiny negative in `as_r1` (approximately -4.13e-8). These are likely floating-point/rounding artifacts, but are flagged and retained in raw data. No values were altered or clipped.

## Initial interpretation — not a conclusion

The all-fund medians are high, while asset-weighted Active Share is materially lower. This means the typical fund and the capital-weighted fund universe produce different pictures. This descriptive contrast does not establish a trend, benchmark pressure, or causality.

## Next research step

1. Produce year-by-year mean, median, asset-weighted Active Share, fund count, and observation count separately for TR and CRSP.
2. Plot paired Russell 1000 and S&P 500 series on aligned axes.
3. Investigate universe composition and identify duplicate share classes / identifier continuity.
4. Apply C.1 classification evidence before calculating active-only results.
5. Do not interpret the TR/CRSP transition as a continuous trend until a provider bridge is evaluated.
