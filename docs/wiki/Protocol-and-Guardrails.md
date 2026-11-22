# Protocol and Guardrails

The authoritative specification is [research/RESEARCH_PROTOCOL.md](https://github.com/tyoungg/market-structure-lab/blob/RUSSEL_SP/research/RESEARCH_PROTOCOL.md). This page summarizes operating rules; it does not supersede the protocol.

## Interpretation rules
- Test the hypothesis; do not assume passive capital or institutional incentives cause mispricing.
- Correlation, simulation, benchmark overlap, or plausible mechanism is not causal proof.
- Preserve negative, null, failed, and mixed results.
- Separate observed data, descriptive statistics, model output, simulation, and hypothesis.
- Do not silently change samples, definitions, benchmarks, date windows, providers, or exclusions.
- Do not call a fund active only because its Active Share is high.
- N-SAR Item 69 = N is not an active label. Unknown is neither active nor passive.
- Keep 5% and 20% Active Share floor samples distinct.
- The 83% dollar-weighted reallocation claim is not validated on a verified active-only sample.
- Keep TR and CRSP separate until their provider bridge is validated.
- Retain the failed size-gradient prediction.
- Label uncalibrated simulations as simulations, not observed data.

## Temporal evidence
For filing-derived labels, verify both filing date and reported period. Both must precede the observation cutoff and evidence freshness must be explicit. Later prospectuses cannot label earlier observations. Registrant-level answers cannot be assigned to every series.

## Deviations
Record date, reason, affected workstream, expected bias/impact, approval, and resolution. Code, source data, and reports must permit independent reproduction.
