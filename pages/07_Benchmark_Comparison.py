import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.rational_coward_data import available_files, load_dataset, find_column

st.set_page_config(page_title="S&P 500 vs Russell 1000", layout="wide")
st.title("S&P 500 vs Russell 1000")
st.markdown("Both benchmarks are **primary comparisons**. This page will not substitute one benchmark for the other or pool TR and CRSP provider periods without a documented bridge.")
files = available_files()
if not files:
    st.info("Awaiting verified source files in `data/public_active_share/`. No benchmark results are shown until the raw data is present.")
    st.markdown("**Required analysis:** benchmark-specific Active Share trends, matched/style-controlled comparisons, source-separated TR and CRSP panels, and uncertainty/sensitivity checks.")
    st.stop()
choice = st.selectbox("Source file", files, format_func=lambda p: p.name)
df = load_dataset(choice)
sp_col = find_column(df, ["as_s5", "active_share_sp500", "sp500_active_share", "s&p 500"])
r1_col = find_column(df, ["as_r1", "active_share_russell1000", "russell_1000_active_share", "russell 1000"])
if sp_col is None or r1_col is None:
    st.warning("Could not identify both S&P 500 and Russell 1000 Active Share columns using known names. Inspect the raw fields below; no automatic assumption was made.")
else:
    st.write(f"Detected columns: **S&P 500:** {sp_col} · **Russell 1000:** {r1_col}")
    st.dataframe(df[[sp_col, r1_col]].describe().T, use_container_width=True)
    st.subheader("Distribution comparison")
    st.line_chart(df[[sp_col, r1_col]].dropna().reset_index(drop=True))
st.subheader("Source fields")
st.write(list(map(str, df.columns)))
