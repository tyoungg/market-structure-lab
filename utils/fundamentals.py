import pandas as pd
import yfinance as yf
import os

CACHE_PATH = "data/cached_fundamentals.parquet"

def get_fundamentals(ticker, at_date=None):
    """
    Fetches fundamental data for a single ticker from yfinance.
    If at_date is provided, attempts to fetch historical data (Version 2).
    NOTE: Currently still relies largely on point-in-time info from yfinance.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info

        # Base fundamentals
        data = {
            "ticker": ticker,
            "sector": info.get("sector"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "revenue_growth": info.get("revenueGrowth"),
            "operating_margin": info.get("operatingMargins"),
            "liquidity": info.get("averageVolume"),
            "momentum": info.get("fiftyTwoWeekChange")
        }

        # If at_date is provided, we could try to fetch historical market cap
        # data = get_historical_fundamentals(ticker, at_date) # Future implementation

        return data
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
