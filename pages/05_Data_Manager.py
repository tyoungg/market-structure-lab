import streamlit as st
import pandas as pd
import os
from utils.fundamentals import build_fundamental_universe, load_fundamental_universe
from utils.price_data import download_price_history, save_price_history
from utils.data_loader import update_sp500_changes, update_dow_changes

st.title("Data Manager")

st.header("1. Fundamental Universe")

universe = load_fundamental_universe()
if universe is not None:
    st.success(f"Universe loaded with {len(universe)} tickers.")
    st.dataframe(universe.head())
else:
    st.warning("No fundamental universe found.")

if st.button("Load Current S&P 500 Tickers"):
    from utils.data_loader import get_current_sp500_constituents
    current_sp = get_current_sp500_constituents()
    if current_sp:
        st.session_state['ticker_list'] = ",".join(sorted(list(current_sp)))
    else:
        st.error("Could not fetch S&P 500 constituents.")

default_tickers = "AAPL,MSFT,GOOGL,AMZN,META,TSLA,BRK-B,V,JNJ,WMT"
tickers_input = st.text_area("Tickers to include in universe (comma-separated)",
                            value=st.session_state.get('ticker_list', default_tickers))

if st.button("Build/Update Universe"):
    tickers = [t.strip() for t in tickers_input.split(",")]
    with st.spinner("Fetching fundamentals..."):
        df = build_fundamental_universe(tickers)
        st.success(f"Built universe with {len(df)} tickers.")
        st.dataframe(df)

st.header("2. Index Changes Data")

col1, col2 = st.columns(2)

with col1:
    if st.button("Auto-update S&P 500 Changes"):
        with st.spinner("Scraping Wikipedia (S&P 500)..."):
            df = update_sp500_changes()
            if df is not None:
                st.success("S&P 500 changes updated.")
                st.dataframe(df.head())
            else:
                st.error("Failed to update S&P 500.")

with col2:
    if st.button("Auto-update Dow Jones Changes"):
        with st.spinner("Scraping Wikipedia (Dow)..."):
            df = update_dow_changes()
            if df is not None:
                st.success("Dow Jones changes updated.")
                st.dataframe(df.head())
            else:
                st.error("Failed to update Dow Jones.")

st.divider()

uploaded_file = st.file_uploader("Upload Manual Index Changes CSV", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df.head())
    target = st.selectbox("Save as...", ["sp500_changes.csv", "dow_changes.csv"])
    if st.button("Save Uploaded Data"):
        df.to_csv(f"data/{target}", index=False)
        st.success(f"Saved to data/{target}")

st.header("3. Cache Management")

if st.button("Clear Price Cache"):
    for f in os.listdir("cache"):
        if f.endswith(".parquet"):
            os.remove(os.path.join("cache", f))
    st.success("Price cache cleared.")
