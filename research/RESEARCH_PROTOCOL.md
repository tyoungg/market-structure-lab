# The Rational Coward — Research Protocol

**Branch:** `RUSSEL_SP`  
**Status:** Governing specification; no empirical results produced by this document  
**Source:** Further Research Addendum (research edition, November 15, 2026)

## 0. Purpose and guardrails

The research tests—not presumes—the proposition that increasing benchmark-linked assets and commercial penalties for benchmark deviation may reduce established managers' willingness to take active risk, while entrants facing high viable scale may select riskier, attention-generating strategies. The resulting capital allocation could leave less patient, moderately active capital challenging prices.

This is a replication/falsification program. Correlation, simulation, benchmark overlap, or a plausible mechanism is not causal proof.

Guardrails:
- Research scope follows this protocol and the source addendum; technical/data issues are logged only when they block a required test.
- Do not carry results from prior branches into this restart without reproducing and validating them.
- Preserve negative/null results and failed predictions.
- Do not silently change definitions, samples, benchmarks, windows, or source providers.
- Keep observed data, descriptive statistics, model output, and hypotheses clearly distinguished.
- Do not promote, merge, or change other branches as part of this work.

## 1. Workstream register and sequence

| ID | Workstream | Question | Required status/output |
|---|---|---|---|
| C.1 | Active-only classification | Is manager activity changing among verified active funds? | Classification audit, annual distributions, assets-weighted results, matched decomposition, break analysis |
| C.2 | No-trade drift counterfactual | How much Active Share movement is explained by market/index drift versus trading? | Actual vs no-trade Active Share; benchmark-specific panels for S&P 500 and Russell 1000; style controls |
| C.3 | Performance vs flow | How much AUM change comes from investment performance vs subscriptions/redemptions? | Return/flow decomposition with share-class, merger and distribution adjustments |
| C.4 | Provider bridge | Can TR historical and CRSP post-2019 data be joined defensibly? | Provider-specific series, bridge diagnostics, visible break until validated |
| C.5 | Distribution exposure | Does distribution/mandate exposure explain active-risk changes? | Exposure measures, pre-trends, controls, gradient tests |
| C.6 | Entrant selection/survival | Are moderate-risk core entrants selected against relative to high-volatility entrants? | Inception cohort, fees, volatility, flows, survival and capital-raising analysis |
| C.7 | Security-level price discovery | Do benchmark-related ownership shocks produce persistent valuation/return effects? | Russell 1000/2000 migration design, pre/post event analysis, valuation and risk outcomes |
| C.8 | Tier1 economics | Is differentiated, patient investment product economically viable? | Product/channel economics, competition, capacity, cannibalization and contribution margins |

Sequence is deliberate: establish active-fund sample validity (C.1), then test the core counterfactual (C.2). No later workstream is allowed to substitute for or obscure these tests.

## 2. C.1 — Active-only classification (highest priority)

### Required source and linkage
Join Notre Dame TR fund identifiers (`fundno`, `wficn`) and CRSP identifiers (`crsp_portno`, `wficn`) to contemporaneous fund summaries, names, prospectuses, objectives, index indicators, and share-class records. Verify identifier integrity, mergers, and share-class relationships.

### Classification
Each fund must be assigned, with evidence and confidence, to:
- Passive index
- Enhanced index
- Active large-cap core
- Other active/style
- Unclassified

Benchmark proximity alone is not a passive-fund classification. Do not classify a fund as active solely because its measured Active Share exceeds a threshold.

### Outputs
- Classification rules, evidence fields, and review log
- Annual fund counts and asset totals by class
- Active-only Active Share distributions/percentiles and asset-weighted statistics
- Matched-sample and attrition decompositions
- Break and sensitivity diagnostics
- Unclassified counts and their potential impact

Recompute the key series on independently verified active funds. Retain the historical no-floor distribution as a distinct sample. Do not carry forward the 83% dollar-weighted reallocation claim as an active-only result without reproducing it.

## 3. C.2 — No-trade drift counterfactual (core test)

### Question
When a portfolio's Active Share changes over time, what portion is caused by passive price/weight drift in the securities it already owns, and what portion requires actual portfolio trading? Explicitly evaluate benchmark concentration, including top-ten benchmark weights.

### Required inputs
- Dated security-level fund positions and portfolio weights at each starting date
- Security total returns over the holding interval
- Benchmark constituent membership and weights at the applicable dates
- Corporate actions and security identity continuity (splits, mergers, spin-offs, ticker/identifier changes)
- Actual ending fund positions/weights, on comparable dates
- Style classifications and control variables
- Fund identifiers and share-class/portfolio mapping

### Counterfactual construction
For each fund and interval:
1. Validate the start-date holdings, date, weights, and security identities.
2. Apply security-level returns and supported corporate actions to each starting position **without trading**.
3. Re-normalize the resulting portfolio weights, treating cash and missing-return handling explicitly and consistently.
4. Calculate no-trade ending Active Share against the benchmark using a documented, consistent definition.
5. Calculate actual ending Active Share from verified end-date positions against the same benchmark and definition.
6. Compare actual change with mechanical no-trade drift. Report the decomposition and residual; do not label residual as manager intent or skill without further evidence.
7. Report coverage, unresolved identities, exclusions, and sensitivity to the handling of cash, corporate actions, missing securities, and timing.
8. Aggregate using transparent fund-count, equal-weight, and asset-weighted summaries where sample support allows. Preserve fund-level observations for audit.

### Mandatory benchmark replications
This analysis must be run independently and in parallel against **both** benchmarks:

**A. S&P 500 benchmark**
- Benchmark constituents/weights and Active Share calculation use S&P 500 definitions and dated weights.
- Explicitly assess the influence of the S&P 500 top-ten concentration on mechanical drift.
- Document fund style compatibility and controls.

**B. Russell 1000 benchmark**
- Re-run the same counterfactual using Russell 1000 constituents/weights and dated benchmark data.
- Do not reuse S&P 500 benchmark weights or membership.
- Include the same fund universe, interval rules, security-return/corporate-action methodology, and compatible style controls to make the comparison interpretable.
- Document differences in benchmark membership, concentration, style coverage, and sample overlap.

**The Russell 1000 replication is a required primary analysis—not an optional robustness test, future enhancement, or appendix.** The S&P 500 and Russell 1000 results must both be shown in the main report. Where fund styles or mandate benchmarks differ, specify and apply style controls, report overlap, and explain any exclusions.

### Minimum C.2 report outputs
- A paired S&P 500 vs Russell 1000 main-results table
- Actual Active Share change, no-trade Active Share change, and residual/decomposition for each benchmark
- Time-series summaries and fund-level distributions
- Asset-weighted and fund-weighted views, clearly distinguished
- Style-control specification and controlled results
- Benchmark top-ten concentration and sensitivity
- Sample size, overlap, coverage and exclusions for each benchmark
- Corporate-action/identity quality report
- Confidence intervals or other uncertainty quantification where feasible
- Predeclared limitations and null findings

### C.2 acceptance checklist
- [ ] Starting positions, ending positions, returns and dates validated
- [ ] Corporate actions and security continuity addressed
- [ ] No-trade weights reproducibly calculated and normalized
- [ ] Active Share implementation tested against hand-checkable cases
- [ ] S&P 500 analysis completed
- [ ] Russell 1000 analysis completed independently
- [ ] Style controls specified and run
- [ ] Top-ten concentration assessed
- [ ] Coverage and missingness disclosed
- [ ] Fund-weighted and asset-weighted summaries reported
- [ ] Paired benchmark comparison appears in primary report
- [ ] Code, inputs, definitions and outputs reproducible

A technical identity or data issue is a blocker only for the affected observations or analysis. It must not silently become the project's primary objective. Log blockers, quantify their scope, and continue unaffected research work where feasible.

## 4. C.3 — Performance versus flow

Join returns, AUM, distributions, share-class changes, and mergers. Decompose dollar changes into market performance, subscriptions, redemptions/exits, and other explainable changes. Test the mechanical benchmark-overlap/return channel and the flow/endogenous-price-pressure channel separately. Contemporaneous association is not an instrument or causal proof.

## 5. C.4 — Provider bridge and post-2019

TR historical data ends in 2019; CRSP coverage begins March 2020; the discussed extension ends September 2023. Before pooling, validate identities, definitions, assets/units, frequency, coverage, and survivor treatment. Keep provider-specific levels and trends separate and show a visible break until a bridge is validated. Obtain newer holdings and equivalent ETF coverage where possible.

## 6. C.5 — Distribution and enterprise exposure

Measure pre-2013 family-level exposure to defined-contribution plans, consultants, retirement recordkeepers, model platforms, and distribution concentration. Separate legal fiduciary liability (generally plan sponsors/fiduciaries) from hypothesized manager-level economic franchise/mandate risk. Test exposure gradients with pre-trends and controls. AUM alone is not an acceptable proxy for the penalty because the prior size-gradient prediction failed.

## 7. C.6 — Entrant selection and survival

Use verified product inception, initial AUM, costs, net fees, distribution access, realized volatility, closures, and capital raises. Compare modest-alpha/moderate-risk core entrants with high-volatility entrants. Separate survival selection from manager choice and account for ETF entry after 2019. The illustrative Tier1 break-even is not a forecast. Report cohort definitions, survivorship and censoring.

## 8. C.7 — Security-level price discovery

For Russell 1000/2000 migrations:
- Identify flow direction (large-to-small vs micro-to-small) and expected ownership shocks.
- Measure earnings yield, book-to-market, cash-flow yield, fundamentals, and ex-ante anomaly scores.
- Trace 1-, 3-, and 5-year relative returns.
- Explicitly test pre-event drift, post-event persistence, risk changes, and corporate share supply.
- Reproduce Coles–Heath–Ringgenberg anomaly-score findings separately from valuation tests.
- Do not interpret an anomaly null as proof that fundamental valuation is unchanged.

## 9. C.8 — Tier1 commercial thesis

Estimate product-level incremental contribution margins, cannibalization, switching/implementation costs, and competitor response by category (traditional active, passive giants, quantitative managers, model providers). Separate strategy viability scale from capacity after impact, crowding and net fees. Evaluate institutional, RIA/model, SMA and licensing channels separately. Analyze flow-intermediation opportunity independently from the price-discovery undersupply claim. This is a competitive hypothesis, not proof that competitors are absent.

## 10. Completed work and interpretation constraints

### Active Share sensitivity
The no-floor fund-count percentile series is not synonymous with active funds. The 5% and 20% floor series are different samples. Historical S&P 500 asset-weighted slopes were approximately -0.43 percentage points/year (5% floor) and -0.03 (20% floor); matched-survivor reallocation shifts from -10.44 percentage points to approximately zero. The 83% reallocation claim is not validated for an active-only sample. TR and CRSP series must not be joined without the provider bridge.

The size-gradient prediction failed: larger funds did not retreat more decisively. Retain this failure in interpretation.

### Agent-based model
The existing v0.1 simulation is exploratory and uncalibrated to SPIVA, ICI, CRSP, Notre Dame, or QDIA data. Its valuation wedge is model units, not percentage mispricing; its 25% entrant risk cap creates boundary solutions. The high-passive/high-barrier and free-informed-entry comparison illustrates a mechanism, not empirical proof. All simulations and plots must be clearly labeled **simulation—not observed data**.

Required upgrades include expanded risk grids, heterogeneous securities and explicit index flows, finite-capital informed traders, calibration, mechanism ablations, and independent empirical comparisons. Report boundary optima and where the hypothesized wedge disappears.

## 11. Reporting and falsification

Every output must document definitions, denominators, annual raw series, style/benchmark classifications, matched-sample attrition, uncertainty, break-search adjustments, no-trade counterfactuals, source transitions, and code. Preserve null/negative findings.

Explicit disconfirmers include:
1. No meaningful manager-choice component after drift controls.
2. No enterprise/distribution exposure gradient with defensible measures.
3. Informed traders or corporate supply prevent persistent valuation effects after benchmark-driven demand.

## 12. Research gates

**Gate 1 — Protocol audit:** Confirm this document maps to the addendum, with the S&P 500 and Russell 1000 C.2 analyses both mandatory. No code or analysis begins before passing this gate.

**Gate 2 — Data feasibility:** Inventory source access, date coverage, licensing, identifiers, benchmark weights, returns, corporate actions and style data. Produce a data-availability matrix and identify blockers without expanding technical work beyond their scope.

**Gate 3 — C.1 validity:** Validate classification and sample construction before interpreting active-only trends.

**Gate 4 — C.2 core results:** Complete both benchmark replications, style controls, paired outputs and coverage audit before moving to peripheral explanatory work.

**Gate 5 — Subsequent workstreams:** Proceed through C.3–C.8 with explicit deliverables and null-result reporting.

**Gate 6 — Reproducibility review:** Independent check of formulas, sample/benchmark dates, calculations, outputs and code before any claim is promoted to a finding.

## 13. Deviations

Any deviation must be recorded with date, reason, affected workstream, expected bias/impact, approval, and resolution. Data limitations may narrow a test, but cannot silently remove a required benchmark or redefine the hypothesis.
