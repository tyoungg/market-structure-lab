from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import pandas as pd
import numpy as np

def prepare_matching_features(universe_df):
    """
    Cleans and scales features for the matching algorithm.
    """
    features = [
        "market_cap",
        "pe_ratio",
        "revenue_growth",
        "operating_margin"
    ]
    df_clean = universe_df[features].dropna()
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df_clean)
    return pd.DataFrame(scaled_data, index=df_clean.index, columns=features), scaler

def find_twins(target_ticker, universe_df, k=5, exclude_tickers=None):
    """
    Finds k-nearest neighbors for a target ticker within the universe.
    Fixes "all scalar values" error by ensuring target_row is a DataFrame.
    """
    features = [
        "market_cap",
        "pe_ratio",
        "revenue_growth",
        "operating_margin"
    ]

    if target_ticker not in universe_df.index:
        raise ValueError(f"{target_ticker} not found in universe")

    # Ensure target_row is a DataFrame, not a Series
    target_row = universe_df.loc[[target_ticker], features]

    if target_row.isnull().any().any():
        missing = target_row.columns[target_row.isnull().any()].tolist()
        raise ValueError(f"{target_ticker} has missing features: {missing}")

    pool = universe_df.drop(target_ticker, errors='ignore')
    if exclude_tickers:
        # Normalize tickers for exclusion
        exclude_set = {str(t).split(' ')[0] for t in exclude_tickers}
        pool = pool.drop(index=[t for t in pool.index if t in exclude_set], errors='ignore')

    pool = pool[features].dropna()

    if len(pool) < k:
        raise ValueError(f"Matching pool too small ({len(pool)}) to find {k} twins.")

    scaler = StandardScaler()
    X = scaler.fit_transform(pool)

    # transform requires a 2D array or DataFrame
    target_scaled = scaler.transform(target_row)

    nn = NearestNeighbors(n_neighbors=k)
    nn.fit(X)

    distances, indices = nn.kneighbors(target_scaled)

    return pool.iloc[indices[0]]
