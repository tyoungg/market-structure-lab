# Research Agents

This repository contains specialist GitHub Copilot custom agents in `.github/agents/`. They are reusable role definitions, not autonomous background jobs. They can be selected in supported Copilot experiences and may be delegated to by a parent agent depending on the product.

| Agent | Role | Authority |
|---|---|---|
| Research Protocol Guardian | Checks alignment with protocol and workstream sequence | Read-only |
| Data Provenance Auditor | Audits source lineage, identifiers, dates, joins, denominators | Read-only |
| Empirical Skeptic | Challenges claims, alternatives, and failed predictions | Read-only |
| Reproducibility Engineer | Builds bounded scripts, tests, and workflows | Can edit/execute when asked |
| Wiki Curator | Documents validated findings with provenance and caveats | Documentation edits |

## Suggested review sequence
1. Protocol Guardian: does the task fit the protocol?
2. Data Provenance Auditor: are source, identifiers, timing, and coverage valid?
3. Reproducibility Engineer: can the test be implemented in a small, bounded, reproducible way?
4. Empirical Skeptic: what alternative explanation or falsification could overturn the result?
5. Wiki Curator: document only the validated result, linking the exact run and audit report.

All agents inherit `.github/copilot-instructions.md`. The governing research protocol remains authoritative.
