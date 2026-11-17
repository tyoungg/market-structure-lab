from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Streamlit Cloud may execute a multipage script with pages/ as its import
# root. Add the repository root explicitly so the shared utils package resolves.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.nport_dashboard import load_dashboard_data

st.set_page_config(page_title="N-PORT No-Trade Counterfactual", page_icon="📊", layout="wide")
st.title("N-PORT No-Trade Counterfactual")
st.caption("Research prototype · read-only display of versioned outputs · research branch only")

data = load_dashboard_data()
summary = data.get("summary", {})
results = data["results"].copy()
availability = data["availability"].copy()
funds = data["funds"].copy()
uncovered = data["uncovered"].copy()

st.warning(
    "**Research status:** descriptive feasibility analysis, not causal evidence. "
    "The benchmark is IVV's reported N-PORT holdings (a tracker-fund proxy), not official S&P 500 weights. "
    "Only the common-equity sleeve is modeled."
)

if not data["available"]:
    st.info(
        "The panel output files have not yet been published to this branch. "
        "The data pipeline is separate from this app; this page will display results after a successful "
        "pipeline run publishes its compact summary files. No results are being estimated or fabricated here."
    )
    if not funds.empty:
        st.subheader("Current screened cohort")
        st.write(f"{len(funds)} prospectus-screened active large-cap mutual-fund series.")
        st.dataframe(funds[["FUND_NAME", "STYLE", "CLASSIFICATION_STATUS", "JUNE_2026_NET_ASSETS_USD"]], use_container_width=True, hide_index=True)
    st.markdown(
        """
        **Panel design:** 11 funds screened using June 2026 assets and public prospectus evidence; four report dates
        (September 2025 through June 2026), creating up to 33 fund-quarter intervals. This is a purposive,
        survivorship- and size-biased feasibility cohort—not a representative universe.
        """
    )
    st.stop()

expected = int(summary.get("expected_fund_intervals", 0))
observed = int(summary.get("observed_fund_intervals", 0))
calculated = int(summary.get("strict_no_trade_intervals_calculated", 0))
withheld = int(summary.get("intervals_withheld_for_incomplete_coverage", 0))
missing = int(summary.get("missing_fund_or_benchmark_observations", 0))
coverage = summary.get("mean_return_coverage")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Expected intervals", f"{expected:,}")
c2.metric("Observed intervals", f"{observed:,}")
c3.metric("Strict estimates", f"{calculated:,}")
c4.metric("Withheld", f"{withheld:,}")
c5.metric("Mean return coverage", f"{coverage:.1%}" if isinstance(coverage, (int, float)) else "—")

if observed < expected or missing:
    st.warning(f"Panel is incomplete: {observed} of {expected} expected intervals observed; {missing} intervals lack a fund or benchmark observation.")
if calculated == 0:
    st.error("No strict no-trade intervals passed the complete-return-coverage rule. The app will not display a panel effect estimate.")

tabs = st.tabs(["Panel results", "Fund explorer", "Data quality", "Methodology"])

with tabs[0]:
    st.subheader("Actual trading versus no-trade drift")
    st.caption("Outcome = actual ending Active Share − no-trade ending Active Share, both versus the same-date IVV holdings proxy. Negative values mean closer to the proxy after actual trading.")
    usable = results[results["STATUS"].eq("CALCULATED")].copy() if "STATUS" in results else pd.DataFrame()
    if usable.empty:
        st.info("There are no intervals with complete starting-position return coverage. See Data quality for the withheld intervals.")
    else:
        usable["DELTA_PP"] = pd.to_numeric(usable["ACTUAL_MINUS_NO_TRADE_ACTIVE_SHARE"], errors="coerce") * 100
        usable["ACTUAL_AS_PCT"] = pd.to_numeric(usable["ACTUAL_END_ACTIVE_SHARE_VS_IVV"], errors="coerce") * 100
        usable["NO_TRADE_AS_PCT"] = pd.to_numeric(usable["NO_TRADE_ACTIVE_SHARE_VS_IVV"], errors="coerce") * 100
        style_filter = st.multiselect("Style", sorted(usable["STYLE"].dropna().unique()), default=sorted(usable["STYLE"].dropna().unique()))
        filtered = usable[usable["STYLE"].isin(style_filter)]
        st.bar_chart(filtered, x="END_DATE", y="DELTA_PP", color="STYLE")
        display_cols = ["FUND_NAME", "STYLE", "START_DATE", "END_DATE", "ACTUAL_AS_PCT", "NO_TRADE_AS_PCT", "DELTA_PP", "RETURN_COVERAGE_START_EQUITY_WEIGHT", "STATUS"]
        st.dataframe(filtered[display_cols].rename(columns={
            "ACTUAL_AS_PCT": "Actual ending AS (%)",
            "NO_TRADE_AS_PCT": "No-trade ending AS (%)",
            "DELTA_PP": "Actual − no-trade (pp)",
            "RETURN_COVERAGE_START_EQUITY_WEIGHT": "Starting equity return coverage",
        }), use_container_width=True, hide_index=True)
    st.download_button("Download interval results CSV", results.to_csv(index=False).encode("utf-8"), "nport_fund_interval_results.csv", "text/csv")

with tabs[1]:
    st.subheader("Fund explorer")
    if not results.empty:
        names = sorted(results["FUND_NAME"].dropna().unique())
        selected_name = st.selectbox("Select fund", names)
        fund_rows = results[results["FUND_NAME"].eq(selected_name)].sort_values("START_DATE").copy()
        for col in ["ACTUAL_END_ACTIVE_SHARE_VS_IVV", "NO_TRADE_ACTIVE_SHARE_VS_IVV"]:
            if col in fund_rows:
                fund_rows[col] = pd.to_numeric(fund_rows[col], errors="coerce") * 100
        st.dataframe(fund_rows, use_container_width=True, hide_index=True)
        chart_rows = fund_rows[fund_rows["STATUS"].eq("CALCULATED")]
        if not chart_rows.empty:
            chart = chart_rows.set_index("END_DATE")[["ACTUAL_END_ACTIVE_SHARE_VS_IVV", "NO_TRADE_ACTIVE_SHARE_VS_IVV"]]
            chart.columns = ["Actual AS (%)", "No-trade AS (%)"]
            st.line_chart(chart)
    if not funds.empty:
        with st.expander("Cohort and classification evidence"):
            st.dataframe(funds, use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("Coverage and filing checks")
    q1, q2, q3 = st.columns(3)
    q1.metric("Missing fund/benchmark observations", missing)
    q2.metric("Intervals withheld", withheld)
    q3.metric("Positions missing returns", f"{len(uncovered):,}")
    if not availability.empty:
        st.markdown("**Expected observation availability**")
        st.dataframe(availability, use_container_width=True, hide_index=True)
    if not uncovered.empty:
        st.markdown("**Starting positions without a validated return**")
        st.dataframe(uncovered, use_container_width=True, hide_index=True)
        st.download_button("Download uncovered positions CSV", uncovered.to_csv(index=False).encode("utf-8"), "nport_uncovered_positions.csv", "text/csv")
    if not data["filings"].empty:
        with st.expander("Selected filing resolution"):
            st.dataframe(data["filings"], use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Calculation and interpretation")
    st.markdown(
        r"""
        For each beginning-period equity position:

        \[
        w^{NT}_{i,t+1}=\frac{w_{i,t}(1+r_{i,t+1})}{\sum_j w_{j,t}(1+r_{j,t+1})}
        \]

        Active Share against the same ending-date benchmark proxy:

        \[
        AS(P,B)=\frac{1}{2}\sum_i |w_{P,i}-w_{B,i}|
        \]

        The reported outcome is **actual ending Active Share minus no-trade ending Active Share**.
        A negative result means actual trading moved the equity sleeve closer to the IVV holdings proxy
        than return drift alone; a positive result means farther away.
        """
    )
    st.markdown("**Rules that matter**")
    st.markdown(
        """
        - The no-trade estimate is withheld unless every beginning equity position has a validated return.
        - Common-equity (ASSET_CAT=EC) holdings are normalized within the equity sleeve; as-filed NAV percentages remain separate.
        - The one-to-many N-PORT identifier bridge is aggregated before joining to holdings.
        - Latest valid original/amended N-PORT filing is selected; late-filing notices are excluded.
        - The calculation assumes proportional treatment of fund flows within the equity sleeve.
        - IVV is a tracker-fund proxy, not official index constituent weights.
        - Yahoo adjusted prices and OpenFIGI mappings are public feasibility sources, not an institutional-grade security master.
        - Foreign listings, FX, delistings, mergers, ticker changes and corporate actions need position-level validation.
        - The selected 11-fund cohort is purposive, size-screened and survivorship-biased; it is not representative.
        - Results are descriptive, not causal.
        """
    )
    st.caption(f"Data source: {summary.get('source_dataset', 'SEC Form N-PORT public data')} · {summary.get('source_note', '')}")
    if summary.get("limitations"):
        with st.expander("Full recorded limitations"):
            for item in summary["limitations"]:
                st.write(f"- {item}")
