import pandas as pd
import yfinance as yf
import os

CACHE_PATH = "data/cached_fundamentals.parquet"

def get_fundamentals(ticker):
    """
    Fetches fundamental data for a single ticker from yfinance.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "ticker": ticker,
            "sector": info.get("sector"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "revenue_growth": info.get("revenueGrowth"),
            "operating_margin": info.get("operatingMargins")
        }
    except Exception as e:
        print(f"Error fetching fundamentals for {ticker}: {e}")
        return None

def build_fundamental_universe(tickers):
    """
    Builds a DataFrame of fundamentals for a list of tickers.
    """
    data = []
    for ticker in tickers:
        f = get_fundamentals(ticker)
        if f:
            data.append(f)

    df = pd.DataFrame(data)
    df.set_index("ticker", inplace=True)
    df.to_parquet(CACHE_PATH)
    return df

def load_fundamental_universe():
    """
    Loads the cached fundamental universe.
    """
    if os.path.exists(CACHE_PATH):
        return pd.read_parquet(CACHE_PATH)
    return None
