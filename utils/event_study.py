import yfinance as yf
import pandas as pd

def get_event_returns(
    ticker,
    benchmark="SPY",
    event_date=None,
    lookback=250,
    lookforward=500
):

    start = pd.to_datetime(event_date) - pd.Timedelta(days=lookback*2)
    end = pd.to_datetime(event_date) + pd.Timedelta(days=lookforward*2)

    stock = yf.download(
        ticker,
        start=start,
        end=end,
        auto_adjust=True
    )["Close"]

    bench = yf.download(
        benchmark,
        start=start,
        end=end,
        auto_adjust=True
    )["Close"]

    df = pd.concat([stock, bench], axis=1)

    df.columns = ["stock", "benchmark"]

    df["stock_return"] = df["stock"] / df["stock"].iloc[0]
    df["benchmark_return"] = df["benchmark"] / df["benchmark"].iloc[0]

    df["abnormal_return"] = (
        df["stock_return"]
        - df["benchmark_return"]
    )

    return df
