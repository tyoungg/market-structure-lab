import streamlit as st

st.set_page_config(page_title="Market Structure Lab", page_icon="📈", layout="wide")
st.title("🏛️ Market Structure Lab")
st.markdown("""## Research tracks

This branch contains a separate research track for **The Rational Coward** hypothesis, alongside the original index-inclusion/Green Score tools.

### The Rational Coward
A falsifiable research program examining benchmark-linked capital, Active Share, manager incentives, entrants, and price discovery. The research dashboard is being built around verified source data; results are not displayed until the raw inputs are audited.

**Primary empirical comparisons:** S&P 500 and Russell 1000. The no-trade drift counterfactual is a central test.

### Original Market Structure tools
Use the existing pages below for event studies, twin analysis, aggregate inclusion analysis, Green Score, and data management.
""")
st.sidebar.info("Use the page navigation to access the research dashboard and legacy tools.")
st.markdown("### Data integrity principles\n- Provider periods are not pooled until the TR–CRSP bridge is validated.\n- Active Share alone does not classify a fund as active or passive.\n- No-trade drift results require holdings, returns, index weights, and corporate actions.\n- Descriptive associations are not causal claims.")
