import streamlit as st
import pandas as pd
from utils.data_loader import load_sp500_changes
from utils.fundamentals import load_fundamental_universe
from utils.event_study import run_event_analysis
from utils.charts import plot_green_score_distribution

st.title("Aggregate Research Engine")

st.markdown("""
This page runs the analysis over all events in the selected dataset to determine if index inclusion
systematically creates excess returns.
""")

dataset = st.selectbox("Select Dataset", ["S&P 500 Additions", "Dow Jones Changes"])

if st.button("Run Aggregate Analysis"):
    events_df = None
    if dataset == "S&P 500 Additions":
        events_df = load_sp500_changes()
    else:
        # Placeholder for Dow
        st.info("Dow Jones analysis coming soon.")

    universe_df = load_fundamental_universe()

    if events_df is None:
        st.error(f"Dataset {dataset} not found. Please upload it in the Data Manager.")
    elif universe_df is None:
        st.error("Fundamental universe not found. Please build it in the Data Manager.")
    else:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        # We only want additions for now
        # Assuming CSV has 'Date' and 'Added' columns
        additions = events_df[events_df['Added'].notnull()]
        total = len(additions)

        for i, (idx, row) in enumerate(additions.iterrows()):
            ticker = row['Added']
            date = row['Date']

            status_text.text(f"Analyzing {ticker} ({i+1}/{total})...")

            res = run_event_analysis(ticker, date, universe_df)
            if res:
                results.append(res)

            progress_bar.progress((i + 1) / total)

        results_df = pd.DataFrame(results)

        if not results_df.empty:
            st.subheader("Aggregate Results")
            st.dataframe(results_df)

            plot_green_score_distribution(results_df)

            avg_score = results_df["green_score"].mean()
            st.metric("Average Green Score", f"{avg_score:.2%}")

            # Save results to session state or disk
            st.session_state['aggregate_results'] = results_df
        else:
            st.warning("No results were generated.")
