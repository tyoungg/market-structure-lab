import streamlit as st
import pandas as pd
from utils.event_study import get_event_window, calculate_abnormal_returns, summarize_event
from utils.charts import plot_event_study
from utils.data_loader import get_index_additions

st.title("Index Inclusion Event Study")

index_source = st.radio("Select Index Source", ["S&P 500", "Dow Jones"], horizontal=True)
index_key = 'sp500' if index_source == "S&P 500" else 'dow'

# Load additions for the dropdown
try:
    additions = get_index_additions(index_type=index_key)
except Exception as e:
    st.error(f"Error loading additions: {e}")
    additions = []

addition_options = ["Manual Input"] + [f"{str(ticker).split(' ')[0]} ({date.strftime('%Y-%m-%d')})" for ticker, date in additions]

selected_option = st.selectbox("Select Index Inclusion Event", options=addition_options)

col1, col2 = st.columns(2)

with col1:
    if selected_option == "Manual Input":
        ticker_val = "TSLA"
    else:
        ticker_val = selected_option.split(" ")[0]

    ticker = st.text_input("Ticker", value=ticker_val)
    alt_ticker = st.text_input("Alternative Ticker (if delisted, e.g. FRCB)", value="")
    final_ticker = alt_ticker if alt_ticker else ticker
    benchmark = st.text_input("Benchmark", value="SPY")

with col2:
    if selected_option == "Manual Input":
        event_date_val = pd.to_datetime("2020-12-21")
    else:
        date_str = selected_option.split("(")[1].split(")")[0]
        event_date_val = pd.to_datetime(date_str)

    event_date = st.date_input("Event Date", value=event_date_val)
    lookback = st.slider("Lookback Days", 50, 500, 250)
    lookforward = st.slider("Lookforward Days", 50, 500, 500)

if st.button("Analyze"):
    with st.spinner(f"Analyzing {final_ticker}..."):
        try:
            # Load data
            stock_df = get_event_window(final_ticker, event_date, before_days=lookback, after_days=lookforward)
            bench_df = get_event_window(benchmark, event_date, before_days=lookback, after_days=lookforward)

            if stock_df.empty:
                st.error(f"No price data found for {final_ticker}. If delisted, try an alternative symbol.")
            elif bench_df.empty:
                st.error(f"No price data found for benchmark {benchmark}.")
            else:
                # Handle MultiIndex
                if isinstance(stock_df.columns, pd.MultiIndex):
                    stock_df.columns = stock_df.columns.get_level_values(0)
                if isinstance(bench_df.columns, pd.MultiIndex):
                    bench_df.columns = bench_df.columns.get_level_values(0)

                # Calculate abnormal returns
                abnormal_returns = calculate_abnormal_returns(stock_df, bench_df)

                # Align for plotting
                common_idx = stock_df.index.intersection(bench_df.index)
                if len(common_idx) < 2:
                    st.error("Insufficient overlapping data between stock and benchmark.")
                else:
                    plot_df = pd.DataFrame({
                        "stock_return": stock_df.loc[common_idx, "Close"] / stock_df.loc[common_idx, "Close"].iloc[0],
                        "benchmark_return": bench_df.loc[common_idx, "Close"] / bench_df.loc[common_idx, "Close"].iloc[0]
                    })

                    plot_event_study(plot_df, final_ticker, benchmark)

                    st.subheader("Event Summary (Abnormal Returns)")
                    summary = summarize_event(abnormal_returns, event_date)
                    st.table(summary)

        except Exception as e:
            st.error(f"Pipeline error: {e}")
            import traceback
            st.code(traceback.format_exc())
