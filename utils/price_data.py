import yfinance as yf
import pandas as pd
import os

CACHE_DIR = "cache"

def get_cache_path(ticker):
    return os.path.join(CACHE_DIR, f"{ticker}.parquet")

def download_price_history(ticker, start, end):
    """
    Downloads price history from Yahoo Finance with robust error handling.
    """
    try:
        df = yf.download(ticker, start=start, end=end, auto_adjust=True)
        if df.empty:
            print(f"Warning: No data found for {ticker} from {start} to {end}.")
            return pd.DataFrame()

        # Flatten MultiIndex if necessary
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df
    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")
        return pd.DataFrame()

def save_price_history(ticker, df):
    """
    Saves price history to a parquet file.
    """
    if df.empty:
        return
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    path = get_cache_path(ticker)
    df.to_parquet(path)

def load_price_history(ticker, start=None, end=None):
    """
    Loads price history from cache if sufficient, otherwise downloads.
    Handles delisted tickers by returning empty DF instead of crashing.
    """
    path = get_cache_path(ticker)
    df = None

    if os.path.exists(path):
        try:
            df = pd.read_parquet(path)
            if start and end:
                start_dt = pd.to_datetime(start)
                end_dt = pd.to_datetime(end)
                if df.index.min() > start_dt or df.index.max() < end_dt:
                    df = None # Cache insufficient
        except:
            df = None

    if df is None:
        df = download_price_history(ticker, start, end)
        if not df.empty:
            save_price_history(ticker, df)

    if df is not None and not df.empty and start and end:
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        mask = (df.index >= start_dt) & (df.index <= end_dt)
        return df.loc[mask]

    return df if df is not None else pd.DataFrame()
