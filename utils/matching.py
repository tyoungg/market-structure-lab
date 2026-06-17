from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import pandas as pd
import numpy as np

def find_twins(target_ticker, universe_df, event_date=None, k=5, exclude_tickers=None, save_matches=True):
    """
    Finds k-nearest neighbors for a target ticker within the universe.
    Uses historical matching metrics: market_cap, liquidity, volatility, momentum.
    """
    import os
    MATCHES_FILE = "data/twin_matches.parquet"
    HISTORICAL_UNIVERSE = "data/historical_universe.parquet"

    features = [
        "market_cap",
        "avg_volume",
        "volatility",
        "momentum"
    ]

    # 1. Determine Pool (Historical or Current)
    pool = universe_df.copy()
    if event_date and os.path.exists(HISTORICAL_UNIVERSE):
        try:
            hist_df = pd.read_parquet(HISTORICAL_UNIVERSE)
            event_year = pd.to_datetime(event_date).year
            pool = hist_df[hist_df['year'] == event_year].set_index('ticker')
            if pool.empty:
                print(f"Warning: No historical data for year {event_year}, falling back to universe_df.")
                pool = universe_df.copy()
        except Exception as e:
            print(f"Error loading historical universe: {e}")

    # 2. Extract Target and Sector
    if target_ticker in pool.index:
        target_row = pool.loc[[target_ticker], features]
        target_sector = pool.loc[target_ticker, 'sector'] if 'sector' in pool.columns else universe_df.loc[target_ticker, 'sector']
    elif target_ticker in universe_df.index:
        target_row = universe_df.loc[[target_ticker], features]
        target_sector = universe_df.loc[target_ticker, 'sector']
    else:
        raise ValueError(f"{target_ticker} not found in universe or historical pool")

    if target_row.isnull().any().any():
        missing = target_row.columns[target_row.isnull().any()].tolist()
        raise ValueError(f"{target_ticker} has missing features: {missing}")

    pool = pool.drop(target_ticker, errors='ignore')

    # 3. Apply Hard Constraints
    if target_sector and 'sector' in pool.columns:
        pool = pool[pool['sector'] == target_sector]

    if exclude_tickers:
        exclude_set = {str(t).split(' ')[0] for t in exclude_tickers}
        pool = pool.drop(index=[t for t in pool.index if t in exclude_set], errors='ignore')

    pool = pool[features].dropna()

    if len(pool) == 0:
        raise ValueError("Matching pool is empty after filtering and dropping NaNs.")

    if len(pool) < k:
        k = len(pool)

    # 4. Nearest Neighbors
    scaler = StandardScaler()
    X = scaler.fit_transform(pool)
    target_scaled = scaler.transform(target_row)

    nn = NearestNeighbors(n_neighbors=k)
    nn.fit(X)

    distances, indices = nn.kneighbors(target_scaled)
    twins = pool.iloc[indices[0]]

    # 5. Save Matches
    if save_matches:
        try:
            match_entry = pd.DataFrame({
                "event_date": [event_date] * k,
                "target": [target_ticker] * k,
                "twin": twins.index.tolist(),
                "distance": distances[0]
            })
            os.makedirs(os.path.dirname(MATCHES_FILE), exist_ok=True)
            if os.path.exists(MATCHES_FILE):
                existing = pd.read_parquet(MATCHES_FILE)
                updated = pd.concat([existing, match_entry]).drop_duplicates()
                updated.to_parquet(MATCHES_FILE)
            else:
                match_entry.to_parquet(MATCHES_FILE)
        except Exception as e:
            print(f"Error saving matches: {e}")

    return twins
