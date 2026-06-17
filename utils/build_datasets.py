import pandas as pd
import os
from utils.data_loader import load_sp500_changes, load_dow_changes
from utils.fundamentals import load_fundamental_universe

def generate_research_datasets():
    print("Generating research datasets...")

    # 1. event_dataset.parquet
    sp500 = load_sp500_changes()
    dow = load_dow_changes()

    events = []
    if sp500 is not None:
        sp_events = sp500[sp500['added_ticker'].notnull()].copy()
        sp_events['index'] = 'SP500'
        events.append(sp_events[['added_ticker', 'event_date', 'index']])

    if dow is not None:
        dow_events = dow[dow['added_ticker'].notnull()].copy()
        dow_events['index'] = 'DOW'
        events.append(dow_events[['added_ticker', 'event_date', 'index']])

    if events:
        event_df = pd.concat(events).rename(columns={'added_ticker': 'ticker'})
        event_df.to_parquet("data/event_dataset.parquet")
        print(f"Saved {len(event_df)} events to data/event_dataset.parquet")
    else:
        print("No events found to save.")

    # 2. matching_universe.parquet
    universe = load_fundamental_universe()
    if universe is not None:
        universe.to_parquet("data/matching_universe.parquet")
        print(f"Saved {len(universe)} tickers to data/matching_universe.parquet")
    else:
        print("No fundamental universe found to save.")

if __name__ == "__main__":
    generate_research_datasets()
