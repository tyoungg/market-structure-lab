# Research Program

The sequence in the [governing Research Protocol](https://github.com/tyoungg/market-structure-lab/blob/RUSSEL_SP/research/RESEARCH_PROTOCOL.md) is substantive: later mechanisms cannot substitute for a valid active-fund sample or the core no-trade counterfactual.

| Workstream | Question | Required output |
|---|---|---|
| C.1 Active-only classification | Is manager activity changing among verified active funds? | Evidence-based classifications, annual distributions, assets-weighted results, attrition and sensitivity |
| C.2 No-trade drift | How much Active Share movement is mechanical drift versus trading? | Actual versus no-trade Active Share, independently for S&P 500 and Russell 1000 |
| C.3 Performance vs. flow | How much AUM change comes from returns versus flows? | Return/flow decomposition with share-class, merger, and distribution adjustments |
| C.4 Provider bridge | Can TR historical and CRSP post-2019 data be joined? | Provider-specific series, bridge diagnostics, visible break until validated |
| C.5 Distribution exposure | Does distribution/mandate exposure explain active-risk changes? | Exposure measures, pre-trends, controls, gradient tests |
| C.6 Entrant selection/survival | Are moderate-risk core entrants selected against? | Inception cohorts, fees, volatility, flows, survival, capital raising |
| C.7 Security-level price discovery | Do benchmark-related ownership shocks affect prices persistently? | Russell 1000/2000 migration design and pre/post-event outcomes |
| C.8 Tier1 economics | Is a differentiated patient-investment product viable? | Product/channel economics, capacity, competition, contribution margins |

## Current priority
The operational [C.1 Active-Fund Classification Protocol](https://github.com/tyoungg/market-structure-lab/blob/RUSSEL_SP/research/ACTIVE_FUND_CLASSIFICATION_PROTOCOL.md) defines positive evidence, as-of timing, conflicts, and the unclassified state. The gate is tracked in [issue #11](https://github.com/tyoungg/market-structure-lab/issues/11).

The immediate C.1 classification gate is tracked in [issue #11](https://github.com/tyoungg/market-structure-lab/issues/11), with acceptance criteria requiring a defensible go/no-go decision rather than a forced active-only result.

C.1 remains the gate. N-SAR Item 69 is a useful positive index-fund signal, but N is not an active label and historical as-of coverage is limited. The corrected extraction has 9 Y fund-years and 181 N-not-active fund-years in the deterministic 80-CIK sample; see [Findings and Falsification](Findings-and-Falsification).

C.2 is the core counterfactual and must be run independently against both the S&P 500 and Russell 1000. The Russell 1000 replication is a required primary analysis, not an optional robustness check.

## Research gates
1. Protocol audit.
2. Data feasibility and provenance.
3. C.1 classification/sample validity.
4. C.2 paired benchmark counterfactuals and style controls.
5. C.3–C.8 subsequent workstreams.
6. Independent reproducibility review.

Scope blockers to the affected observations or analysis. Do not let a technical issue silently become the research question.
