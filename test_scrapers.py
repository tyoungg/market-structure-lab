from utils.data_loader import update_sp500_changes, update_dow_changes, get_index_additions
import pandas as pd
import os

def test_data_collection():
    print("Testing data collection scrapers...")

    # 1. S&P 500
    print("Scraping S&P 500...")
    sp_df = update_sp500_changes()
    if sp_df is not None:
        print(f"S&P 500 changes scraped: {len(sp_df)} rows")
        additions = get_index_additions('sp500')
        print(f"Found {len(additions)} S&P 500 additions.")
        if additions:
            print(f"Latest S&P 500 addition: {additions[0]}")
    else:
        print("S&P 500 scraping failed (likely environment/network).")

    # 2. Dow Jones
    print("\nScraping Dow Jones...")
    dow_df = update_dow_changes()
    if dow_df is not None:
        print(f"Dow Jones changes scraped: {len(dow_df)} rows")
        additions = get_index_additions('dow')
        print(f"Found {len(additions)} Dow Jones additions.")
        if additions:
            print(f"Latest Dow addition: {additions[0]}")
    else:
        print("Dow Jones scraping failed.")

if __name__ == "__main__":
    test_data_collection()
