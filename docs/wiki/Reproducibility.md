# Reproducibility and Audit Trail

## Branch discipline
The current research branch is `RUSSEL_SP`. Do not merge or promote to `main` without explicit approval.

## Workflow references

| Workflow | Purpose | Run |
|---|---|---|
| Active Share baseline | Provider-specific baseline | [44381188999](https://github.com/tyoungg/market-structure-lab/actions/runs/44381188999) |
| Petajisto-to-TR bridge | Historical identifier linkage | [44400738484](https://github.com/tyoungg/market-structure-lab/actions/runs/44400738484) |
| SEC prospectus bridge | Candidate series/class links and sparse filing evidence | [44924324396](https://github.com/tyoungg/market-structure-lab/actions/runs/44924324396) |
| Historical SEC coverage | Bounded 80-CIK coverage probe | [44966589936](https://github.com/tyoungg/market-structure-lab/actions/runs/44966589936) |
| N-SAR header coverage | Contemporaneous identity coverage | [45013756019](https://github.com/tyoungg/market-structure-lab/actions/runs/45013756019) |
| N-SAR Item 69 | Corrected mixed-format parser and series-level index flags | [45017599142](https://github.com/tyoungg/market-structure-lab/actions/runs/45017599142) |

## Acceptance standard

A successful Actions conclusion is only execution status. Before accepting an output:
1. Confirm branch and exact commit.
2. Confirm source artifacts and provenance.
3. Validate schemas, key uniqueness, dates, and denominator.
4. Inspect completion manifests, request errors, unmatched rows, and exclusions.
5. Reconcile output counts to the report.
6. Inspect representative records and edge cases.
7. Confirm the script deadline was not reached and all expected units completed.
8. Link the exact run and preserve the artifact.

## Runtime and data safety
- Use job timeouts and shorter script deadlines.
- Use request timeouts, capped retries, respectful spacing, and checkpoints.
- Keep work on an issue under three hours.
- Do not commit raw source data, credentials, or private data.
- Prefer derived audit metrics and review samples over large raw exports.

## Local N-SAR parser tests

```bash
python -m py_compile scripts/audit_nsar_item69.py
python -m unittest discover -s tests -p 'test_nsar_item69_parser.py'
```

The corrected run processed 282/283 selected answer documents; one SEC 504 retrieval error remains recorded. All 409 report dates parse, including the 32 ISO-formatted rows that were missed by the initial inference path. The corrected as-of panel has 9 positive index-fund Y labels, 181 N-not-active responses, and 22,090 unclassified fund-years. See the exact [workflow run](https://github.com/tyoungg/market-structure-lab/actions/runs/45017599142) and [artifact](https://github.com/tyoungg/market-structure-lab/actions/runs/45017599142/artifacts/14753065280).

## Research management

See [Project Management](Project-Management) for the milestone structure, label taxonomy, Project board fields, and setup workflow.
