import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.rational_coward_data import available_files

st.set_page_config(page_title="Rational Coward Research", layout="wide")
st.title("The Rational Coward — Research Dashboard")
st.caption("A falsifiable research program on benchmark-linked capital, active risk, entrants, and price discovery.")
files = available_files()
c1, c2, c3 = st.columns(3)
c1.metric("Raw datasets found", len(files))
c2.metric("Benchmark tests", "S&P 500 + Russell 1000")
c3.metric("Research status", "Data validation")
st.subheader("Research workstreams")
st.markdown("""- **Active Share baseline:** Reproduce source-specific descriptive trends before interpreting them.
- **Benchmark comparison:** Run S&P 500 and Russell 1000 as paired primary benchmarks.
- **Active-only classification:** Separate passive, enhanced index, active large-cap core, other styles, and unclassified.
- **No-trade drift:** Compare actual holdings evolution with mechanical portfolio drift under both benchmarks.
- **Performance vs. flows:** Separate market returns, fund flows, mergers, and share-class changes.
- **Price discovery:** Test index migration, valuation, fundamentals, and persistence.
""")
if not files:
    st.warning("Data status: no raw public Active Share source files detected in data/public_active_share/. Research results are intentionally withheld until files are audited.")
st.subheader("Current guardrails")
st.markdown("- TR and CRSP periods remain separate until the provider bridge is validated.\n- Active Share benchmark proximity is not an active/passive classification.\n- The no-trade drift counterfactual is a core test, not a sensitivity analysis.\n- Descriptive associations will not be labeled causal without a credible identification design.")
st.subheader("Data directory")
st.code("data/public_active_share/\n  (place original CSV or Parquet source files here; do not commit restricted data)")
