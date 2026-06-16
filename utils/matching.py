from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import pandas as pd

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
    # Drop rows with missing features for matching
    df_clean = universe_df[features].dropna()

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df_clean)

    return pd.DataFrame(scaled_data, index=df_clean.index, columns=features), scaler

def find_twins(target_ticker, universe_df, k=5, exclude_tickers=None):
    """
    Finds k-nearest neighbors for a target ticker within the universe.
    Optional exclude_tickers list to ensure twins are not among index members.
    """
    features = [
        "market_cap",
        "pe_ratio",
        "revenue_growth",
        "operating_margin"
    ]

    # Ensure target_ticker is in universe and has features
    if target_ticker not in universe_df.index:
        raise ValueError(f"{target_ticker} not found in universe")

    target_row = universe_df.loc[[target_ticker], features]

    if target_row.isnull().any().any():
        raise ValueError(f"{target_ticker} has missing features")

    # Exclude the target ticker from the matching pool
    pool = universe_df.drop(target_ticker)

    # Also exclude other index tickers if provided
    if exclude_tickers:
        pool = pool.drop(index=[t for t in exclude_tickers if t in pool.index], errors='ignore')

    pool = pool[features].dropna()

    if len(pool) < k:
        raise ValueError(f"Matching pool too small ({len(pool)}) to find {k} twins.")

    scaler = StandardScaler()
    X = scaler.fit_transform(pool)
    target = scaler.transform(target_row)

    nn = NearestNeighbors(n_neighbors=k)
    nn.fit(X)

    distances, indices = nn.kneighbors(target)

    return pool.iloc[indices[0]]
