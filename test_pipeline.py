import pandas as pd
from utils.data_loader import get_index_tickers_at_date, get_index_additions, update_sp500_changes
from utils.fundamentals import build_fundamental_universe
from utils.matching import find_twins
from utils.event_study import run_event_analysis
import os

def test_full_pipeline():
    print("Starting full pipeline test...")

    # 1. Setup a mini universe
    tickers = ["TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NFLX", "NVDA", "ORCL", "CRM"]
    print("Building mini fundamental universe...")
    universe_df = build_fundamental_universe(tickers)

    # 2. Test dynamic exclusion for TSLA addition on 2020-12-21
    event_date = pd.to_datetime("2020-12-21")

    print(f"Checking index members at {event_date}...")
    update_sp500_changes()

    index_at_event = get_index_tickers_at_date(event_date, index_type='sp500')
    print(f"Index size at event: {len(index_at_event)}")

    # 3. Find twins for TSLA
    print("Finding twins for TSLA (should exclude any index members)...")
    try:
        twins = find_twins("TSLA", universe_df, k=3, exclude_tickers=index_at_event)
        print("Identified Twins:")
        print(twins.index.tolist())

        # Verify
        for twin in twins.index:
            assert twin not in index_at_event, f"Error: Twin {twin} was in the index at the time!"
            assert twin != "TSLA", "Error: Target is in its own twins!"
        print("Twin exclusion verified.")
    except Exception as e:
        print(f"Twin matching failed: {e}")

    # 4. Run full analysis
    print("Running full event analysis orchestration...")
    res = run_event_analysis("TSLA", event_date, universe_df)
    if res:
        print(f"Analysis successful: {res}")
    else:
        print("Analysis failed.")

if __name__ == "__main__":
    test_full_pipeline()
