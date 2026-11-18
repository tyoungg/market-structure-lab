import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.rational_coward_data import available_files, load_dataset, audit_dataset

st.set_page_config(page_title="No-Trade Drift", layout="wide")
st.title("No-Trade Drift Counterfactual")
st.markdown("This is a core empirical test. For each portfolio, advance holdings using security returns and corporate actions **without trading**, then compare the mechanical drift in Active Share with observed Active Share. Repeat separately against S&P 500 and Russell 1000 and use style controls.")
st.warning("The formal test requires dated portfolio holdings, security returns, index constituent weights, and corporate-action handling. Summary Active Share panels alone are not sufficient to calculate no-trade drift.")
files = available_files()
if not files:
    st.info("Raw files are not yet detected. No counterfactual results are generated.")
    st.markdown("**Inputs needed**\n- Dated fund security positions\n- Security-level total returns\n- Benchmark weights for both S&P 500 and Russell 1000\n- Corporate actions and identifier mapping\n- Fund style/classification controls")
    st.stop()
choice = st.selectbox("Inspect available source file", files, format_func=lambda p: p.name)
df = load_dataset(choice)
audit = audit_dataset(df)
st.write(f"Selected file: {choice.name} · {audit['rows']:,} rows · {audit['columns']} columns")
st.caption("This inspection widget does not imply that the file contains the security-level inputs needed for the counterfactual.")
st.dataframe(df.head(50), use_container_width=True)
