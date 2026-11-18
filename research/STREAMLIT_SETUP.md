# Streamlit deployment — RUSSEL_SP

Deploy the research dashboard without touching the repository's default branch.

## Streamlit Community Cloud settings
1. Open Streamlit Community Cloud and choose **New app**.
2. Repository: `tyoungg/market-structure-lab`.
3. Branch: `RUSSEL_SP`.
4. Main file path: `app.py`.
5. Deploy.

The branch's `requirements.txt` already includes Streamlit and the research libraries used by the app. The research pages are additive; the legacy pages remain in the repository.

## Dataset setup
The app looks for CSV or Parquet files under `data/public_active_share/`. Do not commit restricted or licensed datasets. For deployment, use Streamlit secrets or a private external data source only after access permissions and licensing have been reviewed; the current app intentionally does not fetch data from external sources or show unverified results.

## Current limitations
- The baseline page audits and previews files; it does not yet calculate published Active Share statistics.
- The benchmark page only displays basic comparison summaries when matching columns are present. A production analysis needs standardized field mappings and reproducible transformations.
- The no-trade drift page is an input audit shell. The counterfactual requires holdings, security returns, corporate actions, and benchmark constituent weights.
- Raw-data availability and deployment success have not been verified in this environment.
