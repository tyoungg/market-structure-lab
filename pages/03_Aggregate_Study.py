import streamlit as st
import pandas as pd
import os
from utils.data_loader import load_sp500_changes, load_dow_changes, get_current_sp500_constituents, get_current_dow_constituents
from utils.fundamentals import load_fundamental_universe
from utils.event_study import run_event_analysis
from utils.charts import plot_green_score_distribution

st.title("Aggregate Research Engine")

st.markdown("""
This page runs the analysis over all events in the selected dataset to determine if index inclusion
systematically creates excess returns. Results are cached to speed up future runs.
""")

dataset = st.selectbox("Select Dataset", ["S&P 500 Additions", "Dow Jones Changes"])
max_events = st.number_input("Maximum events to analyze", min_value=1, max_value=500, value=10)

RESULTS_FILE = "data/aggregate_results.parquet"

if st.button("Run Aggregate Analysis"):
    events_df = None
    index_key = 'sp500'
    if dataset == "S&P 500 Additions":
        events_df = load_sp500_changes()
        index_key = 'sp500'
    else:
        events_df = load_dow_changes()
        index_key = 'dow'

    universe_df = load_fundamental_universe()

    if events_df is None:
        st.error(f"Dataset {dataset} not found. Please refresh it in the Data Manager.")
    elif universe_df is None:
        st.error("Fundamental universe not found. Please build it in the Data Manager.")
    else:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Prefetch current index members
        with st.spinner(f"Fetching current {index_key} constituents..."):
            if index_key == 'sp500':
                current_index = get_current_sp500_constituents()
            else:
                current_index = get_current_dow_constituents()

        # Filter for additions using normalized columns
        additions = events_df[events_df['added_ticker'].notnull()].copy()
        additions.loc[:, 'event_date'] = pd.to_datetime(additions['event_date'])
        additions = additions.sort_values('event_date', ascending=False).head(max_events)

        # Load existing results if any
        if os.path.exists(RESULTS_FILE):
            try:
                cached_df = pd.read_parquet(RESULTS_FILE)
            except:
                cached_df = pd.DataFrame()
        else:
            cached_df = pd.DataFrame()

        total = len(additions)

        if total == 0:
            st.warning("No addition events found in the dataset.")
        else:
            for i, (idx, row) in enumerate(additions.iterrows()):
                ticker = row['added_ticker']
                date = row['event_date']

                # Check cache first
                if not cached_df.empty:
                    match = cached_df[(cached_df['ticker'] == ticker) & (cached_df['event_date'] == date)]
                    if not match.empty:
                        results.append(match.iloc[0].to_dict())
                        progress_bar.progress((i + 1) / total)
                        continue

                status_text.text(f"Analyzing {ticker} ({i+1}/{total})...")

                res = run_event_analysis(ticker, date, universe_df, current_index=current_index, index_type=index_key)
                if res:
                    results.append(res)

                progress_bar.progress((i + 1) / total)

        results_df = pd.DataFrame(results)
        if not results_df.empty:
            # Update cache
            if cached_df.empty:
                results_df.to_parquet(RESULTS_FILE)
            else:
                updated_cache = pd.concat([cached_df, results_df]).drop_duplicates(subset=['ticker', 'event_date'])
                updated_cache.to_parquet(RESULTS_FILE)

        if not results_df.empty:
            st.subheader("Aggregate Results")
            st.dataframe(results_df)

            plot_green_score_distribution(results_df)

            avg_score = results_df["green_score"].mean()
            st.metric("Average Green Score", f"{avg_score:.2%}")

            # Save results to session state
            st.session_state['aggregate_results'] = results_df
        else:
            st.warning("No results were generated.")
