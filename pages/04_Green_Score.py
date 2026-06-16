import streamlit as st
import pandas as pd
from utils.charts import plot_green_score_distribution

st.title("Green Score Deep Dive")

if 'aggregate_results' not in st.session_state:
    st.info("No aggregate results found. Please run an analysis on the **Aggregate Study** page first.")
else:
    results_df = st.session_state['aggregate_results']

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Winners (Alpha)")
        st.dataframe(results_df.sort_values("green_score", ascending=False).head(10))

    with col2:
        st.subheader("Top Losers (Underperformance)")
        st.dataframe(results_df.sort_values("green_score", ascending=True).head(10))

    st.divider()

    st.subheader("Distribution Analysis")
    plot_green_score_distribution(results_df)

    st.markdown("""
    ### Interpreting the Green Score

    The Green Score represents the excess return of a stock after it has been added to an index,
    relative to its matched "twin" portfolio.

    - **Positive Score**: Consistent with the thesis that index inclusion creates non-fundamental demand and excess return.
    - **Zero/Negative Score**: Suggests the stock's performance is explained by its fundamental characteristics (size, sector, etc.) rather than the inclusion event itself.
    """)
