# Market Structure Lab Copilot instructions

Read `research/RESEARCH_PROTOCOL.md` before changing research code, data definitions, analysis outputs, or conclusions. That protocol is authoritative; Wiki pages summarize it.

## Research guardrails
- Test the thesis; do not presume it. Preserve null, negative, failed, and mixed results.
- Correlation, simulation, benchmark overlap, or plausible mechanism is not causal proof.
- Separate observed data, derived measures, model output, simulation, and hypothesis.
- Do not infer active status from high Active Share or N-SAR Item 69 = N. Unknown is neither active nor passive.
- Keep 5% and 20% Active Share floor samples distinct. No-floor percentiles are not active-only.
- The 83% dollar-weighted reallocation claim is not validated on a verified active-only sample.
- Keep Notre Dame TR and CRSP separate until the provider bridge is independently validated.
- The 2010 SEC registry is a candidate-linkage aid, not proof of historical registration identity.
- N-SAR Item 69 Y is positive index evidence; N is not active evidence. Never spread registrant-level responses across series.
- Filing date and reported period must both precede the observation cutoff. Never backdate evidence.
- Do not silently change samples, definitions, benchmarks, windows, identifiers, or exclusions.

## Engineering guardrails
- Work only on the requested branch (currently `RUSSEL_SP`). Never merge/promote to `main` without explicit approval.
- Public sources only. Do not add WRDS, paid-vendor, private, or institutionally licensed data.
- Never commit raw source datasets, credentials, contact email values, or private data.
- Bound workflows with job timeout, shorter script deadline, request timeouts, capped retries, checkpointing, and a documented denominator.
- Keep total work on an issue under three hours. Prefer small, auditable steps.
- A green Actions run is not proof. Inspect artifacts, denominators, errors, exclusions, dates, and completion manifests.
- Add regression tests for discovered bugs, especially dates, joins, duplicate keys, and as-of logic.
- Do not claim tests, workflows, or publication succeeded unless confirmed.

## Documentation
- Canonical Wiki source is `docs/wiki/`; detailed methods and audits stay in `research/`.
- Publish only verified findings. Label provisional calculations and pending reruns.
- Link empirical claims to the exact source, audit report, and workflow run.
