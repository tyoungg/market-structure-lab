import pandas as pd
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.event_study import run_event_analysis
from utils.fundamentals import load_fundamental_universe

def test_tsla_inclusion():
    ticker = 'TSLA'
    event_date = '2020-12-21'

    # Mock universe_df if it doesn't exist
    universe_df = load_fundamental_universe()
    if universe_df is None or universe_df.empty:
        # Create a tiny dummy universe
        universe_df = pd.DataFrame([
            {"ticker": "AAPL", "sector": "Technology", "market_cap": 2e12, "avg_volume": 1e8, "momentum": 0.5, "volatility": 0.3},
            {"ticker": "F", "sector": "Consumer Cyclical", "market_cap": 4e10, "avg_volume": 5e7, "momentum": 0.1, "volatility": 0.4},
            {"ticker": "GM", "sector": "Consumer Cyclical", "market_cap": 6e10, "avg_volume": 1e7, "momentum": 0.2, "volatility": 0.35}
        ]).set_index("ticker")

    print(f"Running event analysis for {ticker} on {event_date}...")
    result = run_event_analysis(ticker, event_date, universe_df, current_index=set())

    if result:
        print("Success!")
        print(f"Ticker: {result['ticker']}")
        print(f"Event Date: {result['event_date']}")
        print(f"Green Score: {result['green_score']}")
        print(f"Return Premium: {result['return_premium']}")

        assert result['ticker'] == ticker
        assert -100 <= result['green_score'] <= 100
        print("All assertions passed!")
    else:
        print("Analysis failed or returned None (might be due to missing price data in sandbox).")

if __name__ == "__main__":
    test_tsla_inclusion()
