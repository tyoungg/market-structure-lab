# C.2 Security-Level Attribution of the Active Share Residual

**Observation window:** 2025-09-30 to 2025-12-31. **Source snapshot:** validated [GitHub Actions run #20](https://github.com/tyoungg/market-structure-lab/actions/runs/45212700016), branch `RUSSEL_SP`, commit `61084f1e2e48b6737ebae9d3441991c21b5bac5e`. **Scope:** every calculated fund/benchmark pair in the C.2 cohort.

## Method

For each security, the contribution to the portfolio-change residual is `50 × (|actual end weight − benchmark end weight| − |no-trade end weight − benchmark end weight|)`, in percentage points. Summing these contributions exactly reproduces `Active Share(actual fund end, benchmark end) − Active Share(no-trade fund end, benchmark end)`.

Positive contributions increase the residual; negative contributions reduce it. The attribution is benchmark-relative and depends on the absolute-value geometry of Active Share. It is not a return attribution, a trading-volume measure, or evidence of manager intent. The same security can contribute differently against IWB and SPY.

## Fund/benchmark summaries

| Fund | Reviewed context | Benchmark | Securities | Positive sum (pp) | Negative sum (pp) | Net residual (pp) | Top 10 share of absolute contributions |
|---|---|---|---:|---:|---:|---:|---:|
| Fidelity Contrafund | Flexible growth/value | IWB | 447 | +5.246 | -3.586 | +1.660 | 22.0% |
| Fidelity Contrafund | Flexible growth/value | SPY | 447 | +5.235 | -3.703 | +1.531 | 21.7% |
| Fidelity Magellan Fund | Flexible growth/value | IWB | 58 | +4.633 | -4.515 | +0.118 | 55.8% |
| Fidelity Magellan Fund | Flexible growth/value | SPY | 58 | +4.556 | -4.458 | +0.098 | 55.9% |
| JPMorgan Large Cap Growth Fund | Growth; non-diversified since 2025-03-05 | IWB | 78 | +3.420 | -5.056 | -1.635 | 49.4% |
| JPMorgan Large Cap Growth Fund | Growth; non-diversified since 2025-03-05 | SPY | 78 | +3.535 | -5.265 | -1.730 | 49.0% |
| JPMorgan Large Cap Value Fund | Value; non-diversified since 2025-03-05 | IWB | 140 | +14.806 | -15.858 | -1.052 | 23.7% |
| JPMorgan Large Cap Value Fund | Value; non-diversified since 2025-03-05 | SPY | 140 | +14.786 | -15.795 | -1.008 | 23.1% |
| Oakmark Fund | Value; R6 fee-limit change 2025-10-01 | IWB | 57 | +6.584 | -5.654 | +0.929 | 47.8% |
| Oakmark Fund | Value; R6 fee-limit change 2025-10-01 | SPY | 57 | +6.582 | -5.431 | +1.151 | 47.8% |
| Optimum Large Cap Growth Fund | Growth; DMC advisory-agreement/ownership transition 2025-12-01; sub-advisers continued; published split stable | IWB | 146 | +4.800 | -5.944 | -1.144 | 27.1% |
| Optimum Large Cap Growth Fund | Growth; manager transition 2025-12-01 | SPY | 146 | +5.065 | -6.098 | -1.033 | 26.7% |

## What stands out

The residual sign agrees between IWB and SPY for all six funds. The security-level attribution also shows why a small net residual should not be mistaken for small underlying differences: positive and negative name-level contributions can be large and offset one another.

Magellan's residual is only about +0.1 pp, while its gross positive and negative security contributions are each about 4.5 pp; its ten largest absolute name contributions account for roughly 56% of the total absolute contribution. JPMorgan Large Cap Value has gross positive and negative contributions near +14.8 and -15.8 pp, netting to about -1.0 pp. Contrafund and Optimum show more diffuse contributions, with top-ten absolute shares around 22% and 27%, respectively.

The concentration statistic is the top-ten share of the sum of absolute security contributions, not the share of the net residual.

## Largest positive and negative security contributions

### Fidelity Contrafund — IWB

**Positive:** MICROSOFT CORP (+0.197 pp); SPACE EXPLORATION TECHNOLOGIES CORP (+0.179 pp); LOWES COS INC (+0.155 pp); MASTERCARD INC (+0.129 pp); WALT DISNEY CO (+0.122 pp)

**Negative:** META PLATFORMS INC (-0.503 pp); BERKSHIRE HATHAWAY INC DEL (-0.296 pp); AMPHENOL CORPORATION NEW (-0.131 pp); MERCADOLIBRE INC (-0.116 pp); NETFLIX INC (-0.095 pp)

Reconciliation: security contributions +1.659537701 pp; reported residual +1.659537701 pp; error -4.197e-14 pp.

### Fidelity Contrafund — SPY

**Positive:** MICROSOFT CORP (+0.197 pp); SPACE EXPLORATION TECHNOLOGIES CORP (+0.179 pp); LOWES COS INC (+0.155 pp); MASTERCARD INC (+0.129 pp); WALT DISNEY CO (+0.122 pp)

**Negative:** META PLATFORMS INC (-0.503 pp); BERKSHIRE HATHAWAY INC DEL (-0.296 pp); AMPHENOL CORPORATION NEW (-0.131 pp); MERCADOLIBRE INC (-0.116 pp); NETFLIX INC (-0.095 pp)

Reconciliation: security contributions +1.531304954 pp; reported residual +1.531304954 pp; error -4.685e-14 pp.

### Fidelity Magellan Fund — IWB

**Positive:** APOLLO GLOBAL MANAGEMENT, INC (+0.629 pp); VULCAN MATERIALS CO (+0.583 pp); ROLLINS INC (+0.525 pp); TYLER TECHNOLOGIES INC (+0.500 pp); CONSTELLATION ENERGY CORP (+0.499 pp)

**Negative:** MERCADOLIBRE INC (-0.525 pp); UNITED RENTALS INC (-0.489 pp); VERISK ANALYTICS INC (-0.462 pp); PROGRESSIVE CORP OHIO (-0.448 pp); UBER TECHNOLOGIES INC (-0.440 pp)

Reconciliation: security contributions +0.118490443 pp; reported residual +0.118490443 pp; error -6.356e-15 pp.

### Fidelity Magellan Fund — SPY

**Positive:** APOLLO GLOBAL MANAGEMENT, INC (+0.610 pp); VULCAN MATERIALS CO (+0.579 pp); ROLLINS INC (+0.521 pp); TYLER TECHNOLOGIES INC (+0.498 pp); CONSTELLATION ENERGY CORP (+0.487 pp)

**Negative:** MERCADOLIBRE INC (-0.525 pp); UNITED RENTALS INC (-0.483 pp); VERISK ANALYTICS INC (-0.458 pp); WATSCO INC (-0.446 pp); PROGRESSIVE CORP OHIO (-0.432 pp)

Reconciliation: security contributions +0.097639556 pp; reported residual +0.097639556 pp; error -4.649e-15 pp.

### JPMorgan Large Cap Growth Fund — IWB

**Positive:** Alphabet, Inc. (+0.348 pp); Tesla, Inc. (+0.257 pp); Goldman Sachs Group, Inc. (The) (+0.251 pp); Amazon.com, Inc. (+0.249 pp); NVIDIA Corp. (+0.244 pp)

**Negative:** Meta Platforms, Inc. (-1.211 pp); DoorDash, Inc. (-0.483 pp); Netflix, Inc. (-0.411 pp); Oracle Corp. (-0.360 pp); Microsoft Corp. (-0.334 pp)

Reconciliation: security contributions -1.635446580 pp; reported residual -1.635446580 pp; error -3.553e-14 pp.

### JPMorgan Large Cap Growth Fund — SPY

**Positive:** Alphabet, Inc. (+0.348 pp); Ciena Corp. (+0.283 pp); Tesla, Inc. (+0.257 pp); Goldman Sachs Group, Inc. (The) (+0.251 pp); Amazon.com, Inc. (+0.249 pp)

**Negative:** Meta Platforms, Inc. (-1.211 pp); DoorDash, Inc. (-0.483 pp); Netflix, Inc. (-0.411 pp); Eli Lilly & Co. (-0.377 pp); Oracle Corp. (-0.360 pp)

Reconciliation: security contributions -1.730071786 pp; reported residual -1.730071786 pp; error -3.020e-14 pp.

### JPMorgan Large Cap Value Fund — IWB

**Positive:** Berkshire Hathaway, Inc. (+0.641 pp); ICON plc (+0.621 pp); Albemarle Corp. (+0.521 pp); AvalonBay Communities, Inc. (+0.501 pp); Ryder System, Inc. (+0.484 pp)

**Negative:** Western Digital Corp. (-1.617 pp); Seagate Technology Holdings plc (-1.065 pp); Sandisk Corp. (-0.640 pp); Philip Morris International, Inc. (-0.630 pp); Ball Corp. (-0.539 pp)

Reconciliation: security contributions -1.052418662 pp; reported residual -1.052418662 pp; error -5.307e-14 pp.

### JPMorgan Large Cap Value Fund — SPY

**Positive:** ICON plc (+0.621 pp); Berkshire Hathaway, Inc. (+0.542 pp); Albemarle Corp. (+0.519 pp); AvalonBay Communities, Inc. (+0.498 pp); Ryder System, Inc. (+0.496 pp)

**Negative:** Western Digital Corp. (-1.617 pp); Seagate Technology Holdings plc (-0.962 pp); Sandisk Corp. (-0.634 pp); Philip Morris International, Inc. (-0.630 pp); Ball Corp. (-0.538 pp)

Reconciliation: security contributions -1.008436391 pp; reported residual -1.008436391 pp; error -8.438e-15 pp.

### Oakmark Fund — IWB

**Positive:** AerCap Holdings NV (+0.861 pp); Amrize Ltd (+0.625 pp); Corteva Inc (+0.562 pp); Targa Resources Corp (+0.530 pp); CDW Corp/DE (+0.510 pp)

**Negative:** Citigroup Inc (-0.631 pp); Alphabet Inc (-0.590 pp); General Motors Co (-0.536 pp); State Street Corp (-0.520 pp); APA Corp (-0.474 pp)

Reconciliation: security contributions +0.929404556 pp; reported residual +0.929404556 pp; error -5.629e-14 pp.

### Oakmark Fund — SPY

**Positive:** AerCap Holdings NV (+0.861 pp); Amrize Ltd (+0.625 pp); Corteva Inc (+0.562 pp); Targa Resources Corp (+0.530 pp); CDW Corp/DE (+0.508 pp)

**Negative:** Citigroup Inc (-0.631 pp); General Motors Co (-0.536 pp); State Street Corp (-0.520 pp); APA Corp (-0.474 pp); Bank of America Corp (-0.418 pp)

Reconciliation: security contributions +1.151212348 pp; reported residual +1.151212348 pp; error -2.753e-14 pp.

### Optimum Large Cap Growth Fund — IWB

**Positive:** Phillips 66 (+0.419 pp); Booking Holdings Inc (+0.230 pp); Ally Financial Inc (+0.212 pp); Broadcom Inc (+0.206 pp); Cloudflare Inc (+0.198 pp)

**Negative:** Meta Platforms Inc (-0.385 pp); HEICO Corp (-0.357 pp); Gilead Sciences Inc (-0.292 pp); Bank of America Corp (-0.287 pp); Alphabet Inc (-0.259 pp)

Reconciliation: security contributions -1.144373096 pp; reported residual -1.144373096 pp; error +2.576e-14 pp.

### Optimum Large Cap Growth Fund — SPY

**Positive:** Phillips 66 (+0.419 pp); Spotify Technology SA (+0.278 pp); Booking Holdings Inc (+0.230 pp); Ally Financial Inc (+0.214 pp); Broadcom Inc (+0.206 pp)

**Negative:** Meta Platforms Inc (-0.385 pp); HEICO Corp (-0.357 pp); Bank of America Corp (-0.296 pp); Gilead Sciences Inc (-0.275 pp); Alphabet Inc (-0.259 pp)

Reconciliation: security contributions -1.033320767 pp; reported residual -1.033320767 pp; error +2.065e-14 pp.

## Interpretation cautions

This is a security-level decomposition of the Active Share residual, not a causal explanation of why a fund held a security or changed its weight. N-PORT endpoint differences may reflect flows, corporate actions, cash/derivatives, reporting differences, and other effects. Keep each fund's reviewed strategy and structural flags attached to the results. In particular, Optimum's December 1, 2025 event was a DMC advisory-agreement replacement and ultimate-ownership/control change, not a change in the named investment manager. American Century and Los Angeles Capital continued under new agreements, and the published aggregate sleeve split was stable; day-to-day decision continuity is not established. The two JPMorgan funds' non-diversified status changes predate the observation window; Oakmark's flag is a fee-limit change, not an identified strategy change.

The full security-level rows are in `c2_cohort_security_residual_attribution.csv`; the machine-readable pair summaries are in `c2_cohort_security_residual_summary.csv`.