import streamlit as st
import pandas as pd
from utils.matching import find_twins
from utils.portfolio import compare_stock_to_twins
from utils.fundamentals import load_fundamental_universe, get_fundamentals
from utils.charts import plot_stock_vs_twins
from utils.data_loader import get_index_additions, get_index_tickers_at_date

st.title("Counterfactual Twin Analysis")

index_source = st.radio("Select Index Source", ["S&P 500", "Dow Jones"], horizontal=True)
index_key = 'sp500' if index_source == "S&P 500" else 'dow'

# Load additions for the dropdown
try:
    additions = get_index_additions(index_type=index_key)
except Exception as e:
    st.error(f"Error loading additions: {e}")
    additions = []

addition_options = ["Manual Input"] + [f"{ticker} ({date.strftime('%Y-%m-%d')})" for ticker, date in additions]

selected_option = st.selectbox("Select Index Inclusion Event", options=addition_options)

col1, col2 = st.columns(2)

with col1:
    if selected_option == "Manual Input":
        ticker_val = "TSLA"
    else:
        ticker_val = selected_option.split(" ")[0]
    ticker = st.text_input("Ticker", value=ticker_val)
    alt_ticker = st.text_input("Alternative Ticker (if delisted)", value="")
    final_ticker = alt_ticker if alt_ticker else ticker

with col2:
    if selected_option == "Manual Input":
        event_date_val = pd.to_datetime("2020-12-21")
    else:
        date_str = selected_option.split("(")[1].split(")")[0]
        event_date_val = pd.to_datetime(date_str)
    event_date = st.date_input("Event Date", value=event_date_val)

universe_df = load_fundamental_universe()

if universe_df is None:
    st.warning("Fundamental universe not loaded. Please go to Data Manager to build it.")
else:
    if st.button("Find Twins & Compare"):
        try:
            # Check if ticker in universe, if not try to add it
            if ticker not in universe_df.index:
                with st.spinner(f"Ticker {ticker} not in universe. Fetching fundamentals..."):
                    new_f = get_fundamentals(ticker)
                    if new_f:
                        new_row = pd.DataFrame([new_f]).set_index('ticker')
                        universe_df = pd.concat([universe_df, new_row])
                    else:
                        st.error(f"Could not find fundamentals for {ticker}.")
                        st.stop()

            with st.spinner("Finding twins (excluding index members at time of event)..."):
                index_tickers_at_time = get_index_tickers_at_date(event_date, index_type=index_key)
                twins = find_twins(ticker, universe_df, event_date=event_date, exclude_tickers=index_tickers_at_time)

            st.subheader("Identified Twins (Non-Index Members at Event Date)")
            st.dataframe(twins)

            with st.spinner("Building twin portfolio and comparing..."):
                start_date = pd.to_datetime(event_date) - pd.Timedelta(days=250*2)
                end_date = pd.to_datetime(event_date) + pd.Timedelta(days=500*2)

                comparison_df = compare_stock_to_twins(
                    final_ticker,
                    twins.index.tolist(),
                    start_date,
                    end_date
                )

                if not comparison_df.empty:
                    plot_stock_vs_twins(comparison_df, final_ticker)

                    final_stock = comparison_df["stock_return"].iloc[-1]
                    final_twin = comparison_df["twin_return"].iloc[-1]
                    green_score = final_stock - final_twin

                    st.metric("Simple Green Score (End of Window)", f"{green_score:.2%}")
                else:
                    st.error("Could not build comparison data. Check if tickers have data for the requested range.")

        except Exception as e:
            st.error(f"Analysis error: {e}")
            import traceback
            st.code(traceback.format_exc())
