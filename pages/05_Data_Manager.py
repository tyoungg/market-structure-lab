import streamlit as st
import pandas as pd
import os
from utils.fundamentals import build_fundamental_universe, load_fundamental_universe
from utils.price_data import download_price_history, save_price_history
from utils.data_loader import update_sp500_changes

st.title("Data Manager")

st.header("1. Fundamental Universe")

universe = load_fundamental_universe()
if universe is not None:
    st.success(f"Universe loaded with {len(universe)} tickers.")
    st.dataframe(universe.head())
else:
    st.warning("No fundamental universe found.")

tickers_input = st.text_area("Tickers to include in universe (comma-separated)",
                            value="AAPL,MSFT,GOOGL,AMZN,META,TSLA,BRK-B,V,JNJ,WMT")

if st.button("Build/Update Universe"):
    tickers = [t.strip() for t in tickers_input.split(",")]
    with st.spinner("Fetching fundamentals..."):
        df = build_fundamental_universe(tickers)
        st.success(f"Built universe with {len(df)} tickers.")
        st.dataframe(df)

st.header("2. Index Changes Data")

if st.button("Auto-update S&P 500 Changes from Wikipedia"):
    with st.spinner("Scraping Wikipedia..."):
        df = update_sp500_changes()
        if df is not None:
            st.success("S&P 500 changes updated successfully.")
            st.dataframe(df.head())
        else:
            st.error("Failed to update S&P 500 changes.")

st.divider()

uploaded_file = st.file_uploader("Upload Manual S&P 500 Changes CSV", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df.head())
    if st.button("Save S&P 500 Changes"):
        df.to_csv("data/sp500_changes.csv", index=False)
        st.success("Saved to data/sp500_changes.csv")

st.header("3. Cache Management")

if st.button("Clear Price Cache"):
    for f in os.listdir("cache"):
        if f.endswith(".parquet"):
            os.remove(os.path.join("cache", f))
    st.success("Price cache cleared.")
