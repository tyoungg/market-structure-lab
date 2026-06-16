from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

def find_twins(
    target_row,
    universe_df,
    k=5
):

    features = [
        "market_cap",
        "pe_ratio",
        "revenue_growth",
        "operating_margin"
    ]

    scaler = StandardScaler()

    X = scaler.fit_transform(
        universe_df[features]
    )

    target = scaler.transform(
        target_row[features]
    )

    nn = NearestNeighbors(
        n_neighbors=k
    )

    nn.fit(X)

    distances, indices = nn.kneighbors(target)

    return universe_df.iloc[
        indices[0]
    ]
