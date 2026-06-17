import pandas as pd
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.fundamentals import estimate_market_cap, get_avg_volume, get_volatility, get_momentum
from utils.data_loader import get_all_historical_tickers
import yfinance as yf

def build_historical_universe(start_year=2000, end_year=2026):
    print(f"Building historical universe from {start_year} to {end_year}...")
    tickers = get_all_historical_tickers()
    print(f"Total tickers to process: {len(tickers)}")

    # Process from the end to get some diverse tickers
    process_tickers = tickers[-30:]

    rows = []
    for ticker in process_tickers:
        print(f"Processing {ticker}...")
        try:
            t = yf.Ticker(ticker)
            sector = t.info.get('sector')
        except:
            sector = None

        for year in range(start_year, end_year + 1):
            time.sleep(1) # Extra safety
            snapshot_date = pd.to_datetime(f"{year}-06-30")
            if snapshot_date > pd.Timestamp.now():
                snapshot_date = pd.Timestamp.now() - pd.Timedelta(days=1)

            try:
                print(f"  Year {year} at {snapshot_date}")
                mcap = estimate_market_cap(ticker, snapshot_date)
                if mcap is None: continue

                rows.append({
                    "ticker": ticker,
                    "year": year,
                    "sector": sector,
                    "market_cap": mcap,
                    "avg_volume": get_avg_volume(ticker, snapshot_date),
                    "volatility": get_volatility(ticker, snapshot_date),
                    "momentum": get_momentum(ticker, snapshot_date)
                })
            except Exception as e:
                print(f"Error for {ticker} in {year}: {e}")

    if rows:
        df = pd.DataFrame(rows)
        os.makedirs("data", exist_ok=True)
        # Append or overwrite? Let's overwrite for now to be clean
        df.to_parquet("data/historical_universe.parquet")
        print(f"Saved {len(df)} records to data/historical_universe.parquet")
    else:
        print("No records found to save.")

if __name__ == "__main__":
    # For the purpose of this task, we'll run a very small subset
    import time
    # Adding sleep to avoid rate limiting if possible, but for the task we'll just do a tiny slice
    build_historical_universe(start_year=2020, end_year=2026)
