# N-PORT dashboard data

This folder contains compact, versioned outputs published by the N-PORT panel GitHub Actions workflow for the read-only Streamlit dashboard.

It intentionally excludes the large raw holdings extract, per-security return cache, and intermediate weight files. The workflow artifact retains the fuller audit outputs for 30 days.

Files:
- \`panel_summary.json\`: aggregate run counts and descriptive summary.
- \`fund_interval_results.csv\`: one row per fund/quarter interval, including strict-coverage status.
- \`observation_availability.csv\`: expected vs. observed fund and benchmark filings.
- \`uncovered_positions.csv\`: starting positions blocking strict no-trade calculations.
- \`filing_resolution.csv\`: selected accession and filing metadata.
- \`sample_funds.csv\`: prospectus-screened cohort manifest.

The dashboard does not calculate or revise research results. A successful workflow run is required to refresh these files. Do not merge research calculations into the main branch until the data and methodology release gates have passed.
