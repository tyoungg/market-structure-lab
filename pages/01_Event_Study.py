import streamlit as st
import pandas as pd
from utils.event_study import get_event_window, calculate_abnormal_returns, summarize_event
from utils.charts import plot_event_study
from utils.data_loader import get_sp500_additions

st.title("Index Inclusion Event Study")

# Load additions for the dropdown
additions = get_sp500_additions()
addition_options = ["Manual Input"] + [f"{ticker} ({date.strftime('%Y-%m-%d')})" for ticker, date in additions]

selected_option = st.selectbox("Select Index Inclusion Event", options=addition_options)

col1, col2 = st.columns(2)

with col1:
    if selected_option == "Manual Input":
        ticker = st.text_input("Ticker", value="TSLA")
    else:
        ticker_from_opt = selected_option.split(" ")[0]
        ticker = st.text_input("Ticker", value=ticker_from_opt)

    benchmark = st.text_input("Benchmark", value="SPY")

with col2:
    if selected_option == "Manual Input":
        event_date = st.date_input("Event Date", value=pd.to_datetime("2020-12-21"))
    else:
        date_str = selected_option.split("(")[1].split(")")[0]
        event_date = st.date_input("Event Date", value=pd.to_datetime(date_str))

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
                abnormal_returns = calculate_abnormal_returns(stock_df, bench_df)

                # Plot
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
