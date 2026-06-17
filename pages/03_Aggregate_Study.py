import streamlit as st
import pandas as pd
from utils.data_loader import load_sp500_changes, load_dow_changes, get_current_sp500_constituents
from utils.fundamentals import load_fundamental_universe
from utils.event_study import run_event_analysis
from utils.charts import plot_green_score_distribution

st.title("Aggregate Research Engine")

st.markdown("""
This page runs the analysis over all events in the selected dataset to determine if index inclusion
systematically creates excess returns.
""")

dataset = st.selectbox("Select Dataset", ["S&P 500 Additions", "Dow Jones Changes"])
max_events = st.number_input("Maximum events to analyze", min_value=1, max_value=500, value=10)

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

        # Prefetch current index members to avoid redundant network calls in the loop
        with st.spinner(f"Fetching current {index_key} constituents..."):
            if index_key == 'sp500':
                current_index = get_current_sp500_constituents()
            else:
                from utils.data_loader import get_current_dow_constituents
                current_index = get_current_dow_constituents()

        # Filter for additions
        # Dow CSV uses 'Added' and 'Removed', S&P 500 uses 'Added' and 'Removed'
        additions = events_df[events_df['Added'].notnull()].copy()
        additions['Date'] = pd.to_datetime(additions['Date'])
        additions = additions.sort_values('Date', ascending=False).head(max_events)

        total = len(additions)

        if total == 0:
            st.warning("No addition events found in the dataset.")
        else:
            for i, (idx, row) in enumerate(additions.iterrows()):
                ticker = str(row['Added']).split(' ')[0]
                date = row['Date']

                status_text.text(f"Analyzing {ticker} ({i+1}/{total})...")

                res = run_event_analysis(ticker, date, universe_df, current_index=current_index, index_type=index_key)
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
