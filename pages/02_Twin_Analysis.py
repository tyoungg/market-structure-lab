import streamlit as st
import pandas as pd
from utils.matching import find_twins
from utils.portfolio import compare_stock_to_twins
from utils.fundamentals import load_fundamental_universe
from utils.charts import plot_stock_vs_twins
from utils.data_loader import get_all_index_tickers, get_sp500_additions, get_index_tickers_at_date

st.title("Counterfactual Twin Analysis")

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

with col2:
    if selected_option == "Manual Input":
        event_date = st.date_input("Event Date", value=pd.to_datetime("2020-12-21"))
    else:
        date_str = selected_option.split("(")[1].split(")")[0]
        event_date = st.date_input("Event Date", value=pd.to_datetime(date_str))

universe_df = load_fundamental_universe()

if universe_df is None:
    st.warning("Fundamental universe not loaded. Please go to Data Manager to build it.")
else:
    if st.button("Find Twins & Compare"):
        try:
            with st.spinner("Finding twins (excluding index members at time of event)..."):
                # Use dynamic exclusion based on the specific event date
                index_tickers_at_time = get_index_tickers_at_date(event_date)
                twins = find_twins(ticker, universe_df, exclude_tickers=index_tickers_at_time)

            st.subheader("Identified Twins (Non-Index Members at Event Date)")
            st.dataframe(twins)

            with st.spinner("Building twin portfolio and comparing..."):
                start_date = pd.to_datetime(event_date) - pd.Timedelta(days=250*2)
                end_date = pd.to_datetime(event_date) + pd.Timedelta(days=500*2)

                comparison_df = compare_stock_to_twins(
                    ticker,
                    twins.index.tolist(),
                    start_date,
                    end_date
                )

                if not comparison_df.empty:
                    plot_stock_vs_twins(comparison_df, ticker)

                    # Calculate Green Score at end
                    final_stock = comparison_df["stock_return"].iloc[-1]
                    final_twin = comparison_df["twin_return"].iloc[-1]
                    green_score = final_stock - final_twin

                    st.metric("Simple Green Score (End of Window)", f"{green_score:.2%}")
                else:
                    st.error("Could not build comparison data.")

        except Exception as e:
            st.error(f"Error: {e}")
