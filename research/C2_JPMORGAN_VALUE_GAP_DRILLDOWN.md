# C.2 JPMorgan Large Cap Value: Actual-versus-No-Trade Gap Drilldown

**Window:** 2025-09-30 to 2025-12-31  
**Source:** Run #20 artifact `c2-multifund-nport-cohort`, `c2_cohort_fund_security_drift.csv`, `c2_cohort_unpriced_return_sensitivity.csv`.

## 1. What the 36.472% gap measures

The reported actual-versus-no-trade end-portfolio gap is exactly one-half the sum of absolute security-weight differences:

- Sum of absolute actual-minus-no-trade differences: **72.9436 percentage points**.
- Half that sum (the total-variation distance): **36.4718%**, which rounds to the reported **36.472%**.

This is a distance between two normalized end portfolios, not turnover, not the Active Share residual, and not a causal estimate of trading. It is not additive as a list of transactions.

The portfolio contains 140 security identifiers in the union of the starting no-trade portfolio and actual end portfolio.

## 2. Where the gap comes from

| Security relationship | Count | Sum absolute weight difference (pp) | Contribution to half-L1 gap (pp) | Share of total gap |
|---|---:|---:|---:|---:|
| Present at both endpoints; weight differs from no-trade | 66 | 27.351 | 13.675 | 37.50% |
| Start-only relative to actual end (actual end weight zero) | 35 | 22.763 | 11.382 | 31.21% |
| End-only relative to starting no-trade portfolio | 39 | 22.829 | 11.415 | 31.30% |
| **Total** | **140** | **72.944** | **36.472** | **100.00%** |

“Start-only” and “end-only” describe the observed endpoint holdings relative to the no-trade baseline. They must not be relabeled as confirmed sells or purchases: corporate actions, security identity changes, filing/reporting differences, and other effects can also affect endpoint membership.

The continuing-name bucket is also meaningful: even among 66 securities present in both, their actual end weights differ from the price-drifted no-trade weights by 27.351 pp in aggregate absolute terms.

## 3. Largest individual differences

Positive values mean actual end weight exceeds no-trade end weight; negative values mean it is below no-trade end weight.

| Security | Difference (pp) | Endpoint relationship |
|---|---:|---|
| Western Digital | -3.234 | Present at both; actual weight below no-trade |
| Berkshire Hathaway | +2.298 | Present at both; actual weight above no-trade |
| Seagate Technology | -2.129 | Start-only |
| Micron Technology | +1.788 | End-only |
| Sandisk | -1.382 | Start-only |
| Philip Morris International | -1.260 | Present at both; actual weight below no-trade |
| ICON plc | +1.243 | End-only |
| Cigna | -1.168 | Start-only |
| Ball Corp. | -1.125 | Start-only |
| Albemarle | +1.095 | End-only |

The ten largest absolute differences contribute **8.362 pp** to the 36.472% half-L1 gap (about **22.93%**). No single name dominates the entire distance. Western Digital is the largest individual underweight relative to the no-trade path; Berkshire Hathaway is the largest overweight.

## 4. Missing-price sensitivity

One starting security in this fund was unpriced: **Comerica**, representing **0.6413%** of starting equity weight, retained at a zero-return baseline. The artifact's -100%, 0%, and +100% sensitivity results show:

| Assumed Comerica return | Actual vs no-trade gap (%) | Residual vs IWB (pp) | Residual vs SPY (pp) |
|---|---:|---:|---:|
| -100% | 36.266 | -1.047 | -0.985 |
| 0% baseline | 36.472 | -1.052 | -1.008 |
| +100% | 36.675 | -1.075 | -1.031 |

The gap remains large across the full sensitivity range (36.266%–36.675%). The negative residual sign is also unchanged for both benchmark proxies. The missing price therefore does not explain away the large portfolio distance or reverse the residual direction.

## 5. Interpretation with the structural flag

JPMorgan Large Cap Value became non-diversified effective **2025-03-05**, before the C.2 observation window. That legal status permits greater issuer concentration, but this endpoint comparison does not establish that the status change caused the 2025 Q4 portfolio differences. The next useful inquiry is security-level attribution and, if earlier holdings are available, a longer time series around the March 2025 status change.

This is a descriptive holdings comparison. Do not infer manager trading, intent, or causation from the gap. The decomposition residual (approximately -1.0 pp) and the portfolio gap (36.472%) answer different questions and should remain separate in all reporting.
