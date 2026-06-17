import pandas as pd
import yfinance as yf
import numpy as np
import os

CACHE_PATH = "data/cached_fundamentals.parquet"

def estimate_market_cap(ticker, as_of_date):
    """
    Estimates historical market cap using Price * Shares.
    """
    try:
        t = yf.Ticker(ticker)
        at_dt = pd.to_datetime(as_of_date)

        # 1. Get Price
        start = at_dt - pd.Timedelta(days=7)
        hist = t.history(start=start, end=at_dt + pd.Timedelta(days=1))
        if hist.empty: return None

        # Ensure indices are unique
        hist = hist[~hist.index.duplicated(keep='first')]
        if hist.index.tz is not None:
            hist.index = hist.index.tz_localize(None)

        target_dt_naive = at_dt.replace(tzinfo=None)
        idx = hist.index.get_indexer([target_dt_naive], method='nearest')[0]
        price = hist.iloc[idx]['Close']

        # 2. Get Shares
        shares_hist = t.get_shares_full(start=at_dt - pd.Timedelta(days=400), end=at_dt + pd.Timedelta(days=1))
        if not shares_hist.empty:
            if isinstance(shares_hist, (pd.Series, pd.DataFrame)):
                shares_hist = shares_hist[~shares_hist.index.duplicated(keep='first')]
            if shares_hist.index.tz is not None:
                shares_hist.index = shares_hist.index.tz_localize(None)
            s_idx = shares_hist.index.get_indexer([target_dt_naive], method='nearest')[0]
            shares = shares_hist.iloc[s_idx]
            return price * shares

        # Fallback to current info if historical shares fail
        info = t.info
        current_shares = info.get("sharesOutstanding")
        if current_shares:
            return price * current_shares

        return None
    except:
        return None

def get_avg_volume(ticker, as_of_date, lookback=60):
    """
    Retrieves historical average daily volume.
    """
    try:
        t = yf.Ticker(ticker)
        end = pd.to_datetime(as_of_date)
        start = end - pd.Timedelta(days=lookback * 2) # Buffer

        df = t.history(start=start, end=end + pd.Timedelta(days=1))
        if df.empty: return None

        return df['Volume'].tail(lookback).mean()
    except:
        return None

def get_volatility(ticker, as_of_date, lookback=252):
    """
    Calculates historical annualized volatility.
    """
    try:
        t = yf.Ticker(ticker)
        end = pd.to_datetime(as_of_date)
        start = end - pd.Timedelta(days=lookback * 2)

        df = t.history(start=start, end=end + pd.Timedelta(days=1))
        if len(df) < 10: return None

        returns = df['Close'].tail(lookback).pct_change().dropna()
        return returns.std() * np.sqrt(252)
    except:
        return None

def get_momentum(ticker, as_of_date, lookback=252):
    """
    Calculates historical momentum (price change %).
    """
    try:
        t = yf.Ticker(ticker)
        end = pd.to_datetime(as_of_date)
        start = end - pd.Timedelta(days=lookback + 10) # Buffer

        df = t.history(start=start, end=end + pd.Timedelta(days=1))
        if len(df) < 2: return None

        relevant = df.tail(lookback)
        return (relevant['Close'].iloc[-1] / relevant['Close'].iloc[0]) - 1
    except:
        return None

def get_fundamentals(ticker, at_date=None):
    """
    Fetches fundamental data for a single ticker from yfinance.
    If at_date is provided, attempts to fetch historical market cap (Price * Shares).
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info

        market_cap = info.get("marketCap")

        if at_date:
            target_dt = pd.to_datetime(at_date) - pd.Timedelta(days=30)
            market_cap = estimate_market_cap(ticker, target_dt)
            liquidity = get_avg_volume(ticker, target_dt)
            momentum = get_momentum(ticker, target_dt)
            volatility = get_volatility(ticker, target_dt)
        else:
            liquidity = info.get("averageVolume")
            momentum = info.get("fiftyTwoWeekChange")
            volatility = None # Info doesn't easily provide annualized vol

        # Base fundamentals
        data = {
            "ticker": ticker,
            "sector": info.get("sector"),
            "market_cap": market_cap,
            "avg_volume": liquidity,
            "momentum": momentum,
            "volatility": volatility
        }

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

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df.set_index("ticker", inplace=True)

    # Ensure data directory exists
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)

    df.to_parquet(CACHE_PATH)
    return df

def load_fundamental_universe():
    """
    Loads the cached fundamental universe.
    """
    if os.path.exists(CACHE_PATH):
        try:
            return pd.read_parquet(CACHE_PATH)
        except:
            return None
    return None
