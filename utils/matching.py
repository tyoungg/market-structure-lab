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

def find_twins(target_ticker, universe_df, k=5):
    """
    Finds k-nearest neighbors for a target ticker within the universe.
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
    pool = pool[features].dropna()

    scaler = StandardScaler()
    X = scaler.fit_transform(pool)
    target = scaler.transform(target_row)

    nn = NearestNeighbors(n_neighbors=k)
    nn.fit(X)

    distances, indices = nn.kneighbors(target)

    return pool.iloc[indices[0]]
