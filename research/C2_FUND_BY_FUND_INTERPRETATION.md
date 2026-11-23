# C.2 Fund-by-Fund Interpretation

**Window:** 2025-09-30 to 2025-12-31  
**Source:** validated [GitHub Actions run #20](https://github.com/tyoungg/market-structure-lab/actions/runs/45212700016), branch `RUSSEL_SP`, commit `61084f1e2e48b6737ebae9d3441991c21b5bac5e`.

## Scope and interpretation rules

This is a purposive six-fund feasibility cohort, not a representative sample. Each documentary strategy group contains only two funds; do not treat group averages as controlled strategy effects.

Keep three decomposition components distinct: fund price drift, benchmark weight change, and actual portfolio change beyond drift (all in percentage points of Active Share). The actual-versus-no-trade end-portfolio gap is a separate distance measure in percent, not the Active Share residual and not turnover.

The residual is descriptive, not causal or synonymous with manager trading. Flows, corporate actions, cash/derivatives, reporting differences, and other effects can contribute. IWB and SPY are ETF holdings proxies, not official index constituent files.

## Results

| Fund | Strategy / structural context | Proxy | Active Share start → end (%) | Fund drift (pp) | Benchmark change (pp) | Residual beyond drift (pp) | Actual vs no-trade gap (%) |
|---|---|---|---:|---:|---:|---:|---:|
| Fidelity Contrafund | Flexible growth/value | IWB | 50.207 → 51.245 | +0.295 | -0.917 | +1.660 | 9.804 |
| Fidelity Contrafund | Flexible growth/value | SPY | 49.616 → 50.463 | +0.267 | -0.952 | +1.531 | 9.804 |
| Fidelity Magellan | Flexible growth/value | IWB | 69.082 → 70.599 | 0.000 | +1.398 | +0.118 | 10.890 |
| Fidelity Magellan | Flexible growth/value | SPY | 66.306 → 68.024 | 0.000 | +1.620 | +0.098 | 10.890 |
| JPMorgan Large Cap Growth | Growth; non-diversified since 2025-03-05 | IWB | 53.439 → 52.420 | -0.264 | +0.880 | -1.635 | 10.385 |
| JPMorgan Large Cap Growth | Growth; non-diversified since 2025-03-05 | SPY | 50.551 → 49.633 | -0.322 | +1.133 | -1.730 | 10.385 |
| JPMorgan Large Cap Value | Value; non-diversified since 2025-03-05 | IWB | 84.044 → 82.271 | +0.079 | -0.799 | -1.052 | 36.472 |
| JPMorgan Large Cap Value | Value; non-diversified since 2025-03-05 | SPY | 83.277 → 81.535 | +0.081 | -0.814 | -1.008 | 36.472 |
| Oakmark | Value; R6 fee-limit change 2025-10-01 | IWB | 90.687 → 90.843 | -0.005 | -0.769 | +0.929 | 12.841 |
| Oakmark | Value; R6 fee-limit change 2025-10-01 | SPY | 90.058 → 90.434 | -0.005 | -0.770 | +1.151 | 12.841 |
| Optimum Large Cap Growth | Growth; manager transition 2025-12-01 | IWB | 52.303 → 50.478 | -0.147 | -0.534 | -1.144 | 12.763 |
| Optimum Large Cap Growth | Growth; manager transition 2025-12-01 | SPY | 49.634 → 48.068 | -0.218 | -0.315 | -1.033 | 12.763 |

## Fund-by-fund interpretation

### Fidelity Contrafund — flexible growth/value
Active Share rose about 1.04 pp versus IWB and 0.85 pp versus SPY. The residual is positive and comparatively large (+1.660/+1.531 pp), partly offset by negative benchmark weight changes (about -0.9 pp); fund price drift contributes +0.27 to +0.30 pp. Both proxies tell the same directional story. The actual end portfolio is 9.804% from the no-trade end portfolio. Prospectus evidence supports flexibility to invest in growth, value, or both; it is neither a pure growth nor conventional blend classification. No strategy or manager change was identified in reviewed materials, which is not proof that every implementation detail was unchanged.

### Fidelity Magellan — flexible growth/value
Active Share rose 1.517 pp versus IWB and 1.718 pp versus SPY. Price drift contributes 0.000 pp; benchmark weight changes (+1.398/+1.620 pp) explain most of the measured increase in this ordered decomposition, with a small positive residual (+0.118/+0.098 pp). Yet the no-trade end-portfolio gap is 10.890%; a small Active Share residual does not mean few or no trades. The prospectus says the adviser is not constrained by a particular style, so “flexible growth/value” is more accurate than “blend.”

### JPMorgan Large Cap Growth — growth; non-diversified status predates the window
Active Share fell 1.019 pp versus IWB and 0.918 pp versus SPY. The residual is negative (-1.635/-1.730 pp), offset in part by positive benchmark weight changes (+0.880/+1.133 pp); fund drift is modestly negative. The no-trade gap is 10.385%. Non-diversified status became effective 2025-03-05, before both endpoints. This changes the legal concentration framework, but does not prove concentration increased during this quarter or explain the residual.

### JPMorgan Large Cap Value — value; non-diversified status predates the window
Active Share fell 1.773 pp versus IWB and 1.742 pp versus SPY. Both benchmark change (-0.799/-0.814 pp) and residual (-1.052/-1.008 pp) are negative; price drift is slightly positive. Its no-trade gap is 36.472%, the cohort's largest. That large portfolio distance and roughly -1.0 pp Active Share residual are different measures: neither is turnover or a direct estimate of manager trading. The March 5, 2025 non-diversified status predates the window; it does not establish the cause of the large gap.

### Oakmark — value; R6 fee-limit change during the window
Active Share rose slightly (+0.156 pp versus IWB; +0.376 pp versus SPY). The residual is positive (+0.929/+1.151 pp), benchmark weight change is negative (about -0.77 pp), and price drift is near zero. The no-trade gap is 12.841%. The R6 expense-limit reduction effective 2025-10-01 is a fee change, not an identified strategy change; there is no basis here to attribute the residual to it.

### Optimum Large Cap Growth — growth; within-window manager/advisory transition
Active Share fell 1.825 pp versus IWB and 1.566 pp versus SPY. All three components are negative; the residual is -1.144/-1.033 pp, price drift -0.147/-0.218 pp, and benchmark change -0.534/-0.315 pp. The no-trade gap is 12.763%. The manager changed from Delaware Management Company to Nomura Investment Management Business Trust effective 2025-12-01. American Century and Los Angeles Capital continued as sub-advisers under new agreements, but unchanged allocations and day-to-day decisions are not established. This within-window governance break makes a stable-manager interpretation inappropriate; the calculation itself remains descriptive.

## Cross-fund observations

- Residual signs agree between IWB and SPY for every fund. This is useful robustness across these two ETF proxies, not proof of benchmark independence.
- Residuals are positive for Contrafund, Magellan, and Oakmark, and negative for both JPMorgan funds and Optimum. The cohort is too small and heterogeneous to infer strategy-group effects.
- The no-trade gap does not rank the residual: JPMorgan Large Cap Value has the largest gap (36.472%) but a residual near -1.0 pp; Magellan has a 10.890% gap but a residual near +0.1 pp.
- Structural flags are not interchangeable: Optimum's manager change is within-window; JPMorgan's legal-status changes predate it; Oakmark's flag is a fee change; Contrafund and Magellan have flexible mandates.
- Do not pool group averages or use post-hoc structural flags to silently exclude funds.

## Recommended next checks

1. Decompose JPMorgan Large Cap Value's 36.472% gap into largest security-level contributors, additions, exits, and weight changes. Keep this separate from the Active Share residual.
2. For Optimum, examine sub-period holdings around the December 1 manager transition if the filing cadence permits; do not assume December 31 holdings reflect only the new manager's decisions.
3. Calculate security-level contributions to the residual for all six funds and test whether a few names dominate, preserving identifier matching and missing-return sensitivity.
4. Then extend the cohort across more quarters/funds, carrying strategy and structural flags forward.

## Validation and limitations

Run #20 validated 24 frozen SEC N-PORT filings, six funds, two ETF proxies, and all 12 decompositions. Each entity passed independent 95% mapping and price-coverage gates; the lowest price coverage was Oakmark at 96.818%. Maximum absolute decomposition reconciliation error was 0.0 pp. Yahoo Finance auto-adjusted closes are exploratory; SPY/IWB are ETF proxies. Keyence (6861.T) lacked an exact December 31 endpoint and was retained as missing, not assigned an invented FX-adjusted return.

See `research/C2_STRATEGY_EVIDENCE_REVIEW.md` and `research/C2_COHORT_FUND_FLAGS.json` for documentary evidence and machine-readable flags. The machine-readable calculation outputs are in the Run #20 artifact `c2-multifund-nport-cohort`.
