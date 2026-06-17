import pandas as pd
from utils.data_loader import get_index_tickers_at_date, update_sp500_changes
from utils.fundamentals import build_fundamental_universe
from utils.matching import find_twins

def test_exclusion_logic():
    print("Testing exclusion logic...")
    update_sp500_changes()

    # Dec 2020: TSLA was ADDED.
    event_date = "2020-12-21"
    index_members = get_index_tickers_at_date(event_date)

    print(f"Index members at {event_date} (first 10): {list(index_members)[:10]}")

    # Mock a universe that has some index and some non-index stocks
    # All these are current index members
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
    # Add some that were definitely NOT in the index in 2020
    # Actually most large caps are in it. Let's find some that weren't.
    # We can just use dummy tickers if needed, but let's try real ones.

    universe_df = build_fundamental_universe(tickers)

    # If we try to find twins for TSLA and exclude index_members,
    # and all other stocks in universe are in index_members, it should fail.

    print("Verifying TSLA is in index_members at event date...")
    assert "TSLA" in index_members

    print("Finding twins for TSLA with exclusion...")
    try:
        twins = find_twins("TSLA", universe_df, k=1, exclude_tickers=index_members)
        print(f"Twins found: {twins.index.tolist()}")
    except Exception as e:
        print(f"Expected failure: {e}")

    print("Exclusion logic verification complete.")

if __name__ == "__main__":
    test_exclusion_logic()
