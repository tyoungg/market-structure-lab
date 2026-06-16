import yfinance as yf
import pandas as pd
import os

CACHE_DIR = "cache"

def get_cache_path(ticker):
    return os.path.join(CACHE_DIR, f"{ticker}.parquet")

def download_price_history(ticker, start, end):
    """
    Downloads price history from Yahoo Finance.
    """
    df = yf.download(ticker, start=start, end=end, auto_adjust=True)
    return df

def save_price_history(ticker, df):
    """
    Saves price history to a parquet file in the cache directory.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    path = get_cache_path(ticker)
    df.to_parquet(path)

def load_price_history(ticker, start=None, end=None):
    """
    Loads price history from cache if available and sufficient, otherwise downloads it.
    """
    path = get_cache_path(ticker)
    df = None

    if os.path.exists(path):
        df = pd.read_parquet(path)

        # Check if the cached data covers the requested range
        if start and end:
            start_dt = pd.to_datetime(start)
            end_dt = pd.to_datetime(end)
            if df.index.min() > start_dt or df.index.max() < end_dt:
                # Cache is insufficient, need to re-download
                df = None

    if df is None:
        # If no start/end provided for download, we might want a default range
        # but here we use what's passed.
        df = download_price_history(ticker, start, end)
        save_price_history(ticker, df)

    if start and end:
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        mask = (df.index >= start_dt) & (df.index <= end_dt)
        return df.loc[mask]

    return df
