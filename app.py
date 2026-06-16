import streamlit as st

st.set_page_config(
    page_title="Market Structure Lab",
    page_icon="📈",
    layout="wide"
)

st.title("🏛️ Market Structure Lab")

st.markdown("""
Welcome to the **Market Structure Lab**. This application is designed to analyze the impact of index inclusions and exclusions on stock performance.

### Core Research Questions
- Do stocks added to major indexes outperform comparable non-added companies?
- Is there a "Green Score" premium associated with index inclusion?
- How does market structure influence individual stock behavior?

### Navigation
Use the sidebar to navigate through different analysis tools:
1. **Event Study**: Analyze individual stock performance around index changes.
2. **Twin Analysis**: Compare a stock against a counterfactual portfolio of similar "twin" stocks.
3. **Aggregate Study**: View research results across hundreds of historical events.
4. **Green Score**: Deep dive into the Green Score distribution and rankings.
5. **Data Manager**: Update price history and fundamental data.

---
*Based on the thesis that market structure and passive flows create systematic performance deviations.*
""")

st.sidebar.success("Select a page above.")
