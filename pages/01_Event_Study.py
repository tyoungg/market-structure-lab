import streamlit as st
import pandas as pd
from utils.event_study import get_event_window, calculate_abnormal_returns, summarize_event
from utils.charts import plot_event_study

st.title("Index Inclusion Event Study")

col1, col2 = st.columns(2)

with col1:
    ticker = st.text_input("Ticker", value="TSLA")
    benchmark = st.text_input("Benchmark", value="SPY")

with col2:
    event_date = st.date_input("Event Date", value=pd.to_datetime("2020-12-21"))
    lookback = st.slider("Lookback Days", 50, 500, 250)
    lookforward = st.slider("Lookforward Days", 50, 500, 500)

if st.button("Analyze"):
    with st.spinner(f"Analyzing {ticker}..."):
        try:
            # Load data
            stock_df = get_event_window(ticker, event_date, before_days=lookback, after_days=lookforward)
            bench_df = get_event_window(benchmark, event_date, before_days=lookback, after_days=lookforward)

            if stock_df.empty or bench_df.empty:
                st.error("Could not retrieve data for the specified ticker or benchmark.")
            else:
                # Calculate abnormal returns
                # We need to ensure we're passing the right thing to calculate_abnormal_returns
                # It currently expects (stock_df, benchmark_df)

                # Align and calculate
                abnormal_returns = calculate_abnormal_returns(stock_df, bench_df)

                # Plot
                # plot_event_study expects (df, ticker, benchmark)
                # But calculate_abnormal_returns returns a Series.
                # Let's adjust to get the full DF for plotting

                plot_df = pd.concat([
                    stock_df["Close"] / stock_df["Close"].iloc[0],
                    bench_df["Close"] / bench_df["Close"].iloc[0]
                ], axis=1).dropna()
                plot_df.columns = ["stock_return", "benchmark_return"]

                plot_event_study(plot_df, ticker, benchmark)

                # Summary Table
                st.subheader("Event Summary (Abnormal Returns)")
                summary = summarize_event(abnormal_returns, event_date)
                st.table(summary)

        except Exception as e:
            st.error(f"An error occurred: {e}")
