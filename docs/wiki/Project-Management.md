# Project Management

This page defines the operational structure for managing the research program. It is a working roadmap, not evidence that a workstream's empirical claims have been validated.

## GitHub Project

Create one repository-linked GitHub Projects v2 board titled **Market Structure Lab — Research Program**. The recommended board fields are:

| Field | Type | Values / use |
|---|---|---|
| Status | Single select | Backlog, Ready, In Progress, Blocked, Validating, Complete |
| Workstream | Single select | C.1 through C.8 |
| Priority | Single select | Critical, High, Medium, Low |
| Evidence status | Single select | Hypothesis, In Progress, Validated, Rejected, Inconclusive |
| Next action | Text | One concrete next step |
| Target milestone | Text or milestone link | Next meaningful deliverable |

Keep **Status** separate from **Evidence status**. A task can be technically complete while the empirical result remains inconclusive. Do not set Evidence status to Validated merely because a GitHub Actions workflow passes.

Recommended views:
1. **Roadmap** — table grouped by Target milestone.
2. **Execution board** — board grouped by Status.
3. **Evidence ledger** — table grouped by Evidence status.
4. **Workstream view** — board or table grouped by Workstream.

Add repository issues to the project; use one issue for a discrete research question, implementation task, audit, or documentation deliverable. Keep the issue's acceptance criteria and falsification checks in its body.

## Repository milestones

The bootstrap workflow creates these milestones if they do not already exist. They are deliverable gates, not arbitrary calendar deadlines.

| Milestone | Scope / exit condition |
|---|---|
| M1 — Reproducible Baseline | Provider-specific source panels, provenance, schema checks, and baseline outputs independently reproducible |
| M2 — Active-Only Classification | Defensible fund-level strategy labels, as-of timing, ambiguity handling, and sample sensitivity documented |
| M3 — Performance and Flows | AUM changes decomposed into performance and net flows with share-class and corporate-action adjustments |
| M4 — Provider Bridge | TR/CRSP identity bridge validated or explicit break retained |
| M5 — Distribution and Survival | Exposure measures, entrant cohorts, survival, pre-trends, and selection tests completed |
| M6 — Russell Migration | Russell 1000/2000 migration event design, pre-trends, placebo tests, and outcome construction audited |
| M7 — Commercial Economics | Tier 1 product/channel economics, capacity, competitive context, and contribution margins assessed |
| M8 — Research Synthesis | Integrated findings, null results, limitations, and reproducibility package completed |

## Label taxonomy

The bootstrap workflow creates a compact label set:

- **Workstream:** `C.1-classification`, `C.2-counterfactual`, `C.3-performance-flows`, `C.4-provider-bridge`, `C.5-distribution`, `C.6-survival`, `C.7-russell-migration`, `C.8-commercial`.
- **Evidence state:** `validated`, `needs-validation`, `failed-test`, `inconclusive`, `falsified`.
- **Task type:** `data`, `methodology`, `code`, `documentation`, `audit`, `publication`.
- **Priority:** `priority-critical`, `priority-high`, `priority-medium`, `priority-low`.

Use one workstream label, one evidence-state label, and one task-type label where applicable. Add a priority label only when it helps sort the backlog. Do not create near-duplicate labels.

## Issue definition of done

A research issue should state:
1. The research question and why it matters.
2. Source data, provenance, and sample/denominator.
3. Method and identification assumptions.
4. Acceptance tests, including dates, keys, missingness, and edge cases.
5. Falsification checks and what the analysis cannot establish.
6. Expected artifacts and the next decision.

Close an issue only when its technical deliverable is complete and its evidence status is separately recorded. Preserve failed, null, and inconclusive outcomes.

## Setup

Run [Bootstrap research labels and milestones](https://github.com/tyoungg/market-structure-lab/actions/workflows/bootstrap-research-management.yml) on branch `RUSSEL_SP`. The workflow is idempotent and creates missing repository labels and milestones without changing existing definitions.

GitHub Projects v2 is a user/organization-level resource and is not created by the repository-scoped bootstrap workflow. Create the board from the repository's **Projects** tab, add the repository as a source, and configure the fields/views above. This repository currently has no open issues, so add new work items as discrete tasks are defined rather than generating empty placeholder issues for all eight workstreams.

## Guardrails

- All research changes remain on `RUSSEL_SP`; do not merge or promote to `main) without explicit approval.
- Do not commit raw source datasets, credentials, or private data.
- Keep each issue/workflow under the three-hour ceiling; target substantially shorter runs.
- A successful workflow is execution evidence, not empirical validation.
- Never treat N-SAR Item 69 N, missing filings, unmatched identities, or absent records as proof of active management.
