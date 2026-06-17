import pandas as pd
import yfinance as yf
import os

CACHE_PATH = "data/cached_fundamentals.parquet"

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
            try:
                at_dt = pd.to_datetime(at_date)
                # 30 days before the event
                target_dt = at_dt - pd.Timedelta(days=30)

                # Fetch price history around that date
                hist = t.history(start=target_dt - pd.Timedelta(days=7),
                                 end=target_dt + pd.Timedelta(days=7))

                if not hist.empty:
                    # Ensure indices are unique for get_indexer
                    hist = hist[~hist.index.duplicated(keep='first')]

                    # Handle timezone alignment
                    if hist.index.tz is not None:
                        hist.index = hist.index.tz_localize(None)
                    target_dt_naive = target_dt.replace(tzinfo=None)

                    # Get closest price to target_dt
                    idx = hist.index.get_indexer([target_dt_naive], method='nearest')[0]
                    price = hist.iloc[idx]['Close']

                    # Fetch share count history
                    shares_hist = t.get_shares_full(start=target_dt - pd.Timedelta(days=60),
                                                   end=target_dt + pd.Timedelta(days=7))

                    if not shares_hist.empty:
                        # Ensure indices are unique
                        if isinstance(shares_hist, pd.Series):
                             shares_hist = shares_hist[~shares_hist.index.duplicated(keep='first')]

                        # Convert both to timezone-naive if they are inconsistent
                        if shares_hist.index.tz is not None:
                            shares_hist.index = shares_hist.index.tz_localize(None)
                        target_dt_naive = target_dt.replace(tzinfo=None)

                        # Get closest share count
                        s_idx = shares_hist.index.get_indexer([target_dt_naive], method='nearest')[0]
                        shares = shares_hist.iloc[s_idx]
                        market_cap = price * shares
                    else:
                        # Fallback to historical price * current shares (if available)
                        current_shares = info.get("sharesOutstanding")
                        if current_shares:
                            market_cap = price * current_shares
            except Exception as e:
                print(f"Error calculating historical market cap for {ticker}: {e}")

        # Base fundamentals
        data = {
            "ticker": ticker,
            "sector": info.get("sector"),
            "market_cap": market_cap,
            "pe_ratio": info.get("trailingPE"),
            "revenue_growth": info.get("revenueGrowth"),
            "operating_margin": info.get("operatingMargins"),
            "liquidity": info.get("averageVolume"),
            "momentum": info.get("fiftyTwoWeekChange")
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
