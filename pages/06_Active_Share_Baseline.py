import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.rational_coward_data import available_files, load_dataset, audit_dataset

st.set_page_config(page_title="Active Share Baseline", layout="wide")
st.title("Active Share Baseline")
st.caption("Descriptive baseline only. Provider periods remain separate until the TR–CRSP bridge is validated.")
files = available_files()
if not files:
    st.warning("Raw Active Share datasets are not currently available in the expected local folder.")
    st.markdown("**Expected folder:** `data/public_active_share/")
    st.markdown("Place the original Notre Dame TR and CRSP files here. This page will read CSV or Parquet files and show an audit before any analysis.")
    st.stop()
choice = st.selectbox("Dataset file", files, format_func=lambda p: p.name)
df = load_dataset(choice)
audit = audit_dataset(df)
cols = st.columns(4)
cols[0].metric("Rows", f"{audit['rows']:,}")
cols[1].metric("Columns", f"{audit['columns']:,}")
cols[2].metric("Duplicate rows", f"{audit['duplicate_rows']:,}")
cols[3].metric("Missing cells", f"{audit['missing_cells']:,}")
st.subheader("Raw-file audit")
st.write("Column names are displayed exactly as read from source.")
st.code("\\n".join(audit["column_names"]))
st.subheader("Preview")
st.dataframe(df.head(100), use_container_width=True)
st.download_button("Download loaded file as CSV", df.to_csv(index=False).encode("utf-8"), file_name=f"{choice.stem}_preview.csv", mime="text/csv")
