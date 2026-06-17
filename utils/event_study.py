import pandas as pd
from .price_data import load_price_history
from .matching import find_twins
from .portfolio import build_twin_portfolio
from .green_score import calculate_return_premium, calculate_green_score
from .data_loader import get_index_tickers_at_date

def get_event_window(ticker, event_date, before_days=250, after_days=500):
    """
    Retrieves the price history for a ticker around an event date.
    """
    event_dt = pd.to_datetime(event_date)
    start = event_dt - pd.Timedelta(days=before_days * 2) # Buffer for trading days
    end = event_dt + pd.Timedelta(days=after_days * 2)

    return load_price_history(ticker, start=start, end=end)

def calculate_abnormal_returns(stock_df, benchmark_df):
    """
    Calculates abnormal returns relative to a benchmark.
    Assumes both dataframes have been aligned by index.
    """
    # Handle multi-index if present
    if isinstance(stock_df.columns, pd.MultiIndex):
        stock_df.columns = stock_df.columns.get_level_values(0)
    if isinstance(benchmark_df.columns, pd.MultiIndex):
        benchmark_df.columns = benchmark_df.columns.get_level_values(0)

    # Align dataframes
    df = pd.concat([stock_df["Close"], benchmark_df["Close"]], axis=1).dropna()
    df.columns = ["stock", "benchmark"]

    # Normalizing to 1.0 at the beginning of the series
    df["stock_return"] = df["stock"] / df["stock"].iloc[0]
    df["benchmark_return"] = df["benchmark"] / df["benchmark"].iloc[0]

    df["abnormal_return"] = df["stock_return"] - df["benchmark_return"]
    return df["abnormal_return"]

def summarize_event(abnormal_returns, event_date):
    """
    Provides a summary table of abnormal returns at specific intervals.
    """
    event_dt = pd.to_datetime(event_date)

    # Finding nearest trading day to event date
    if event_dt not in abnormal_returns.index:
        # Use the closest available date
        idx = abnormal_returns.index.get_indexer([event_dt], method='nearest')[0]
        event_dt = abnormal_returns.index[idx]

    # Calculate performance relative to event_date
    # Find position of event_dt
    event_pos = abnormal_returns.index.get_loc(event_dt)

    windows = [-30, 30, 90, 180, 365]
    summary = {}

    for w in windows:
        target_pos = event_pos + w
        if 0 <= target_pos < len(abnormal_returns):
            summary[f"Day {w}"] = abnormal_returns.iloc[target_pos] - abnormal_returns.iloc[event_pos]
        else:
            summary[f"Day {w}"] = None

    return pd.Series(summary)

def run_event_analysis(ticker, event_date, universe_df, benchmark="SPY", current_index=None, index_type='sp500'):
    """
    Full orchestration for a single event analysis.
    """
    try:
        # 1. Get Event window
        stock_df = get_event_window(ticker, event_date)
        bench_df = get_event_window(benchmark, event_date)

        # 2. Find Twins (excluding index members at the time of the event)
        index_tickers = get_index_tickers_at_date(event_date, index_type=index_type, current_tickers=current_index)
        twins = find_twins(ticker, universe_df, exclude_tickers=index_tickers)
        twin_tickers = twins.index.tolist()

        # 3. Build Twin Portfolio
        event_dt = pd.to_datetime(event_date)
        start = event_dt - pd.Timedelta(days=250*2)
        end = event_dt + pd.Timedelta(days=500*2)
        twin_portfolio = build_twin_portfolio(twin_tickers, start, end)

        # 4. Calculate Returns
        # Handle multi-index if present
        if isinstance(stock_df.columns, pd.MultiIndex):
            stock_df.columns = stock_df.columns.get_level_values(0)

        # We need to align stock_df and twin_portfolio
        common_index = stock_df.index.intersection(twin_portfolio.index)
        stock_returns = stock_df.loc[common_index, "Close"] / stock_df.loc[common_index, "Close"].iloc[0]
        twin_returns = twin_portfolio.loc[common_index] # Already normalized in build_twin_portfolio?
        # Actually build_twin_portfolio returns normalized mean.

        # Calculate Green Score at end of window or specific point?
        # Let's say +365 days or last available.
        stock_final = stock_returns.iloc[-1]
        twin_final = twin_returns.iloc[-1]

        green_score = calculate_green_score(stock_final, twin_final)

        return {
            "ticker": ticker,
            "event_date": event_date,
            "green_score": green_score
        }
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None
