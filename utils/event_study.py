import pandas as pd
from .price_data import load_price_history
from .matching import find_twins
from .fundamentals import get_fundamentals, build_fundamental_universe
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
    Full orchestration for a single event analysis (Version 2).
    """
    import os
    import numpy as np
    try:
        # 0. Ensure ticker is in universe
        if ticker not in universe_df.index:
            print(f"Ticker {ticker} missing from universe, attempting to fetch...")
            new_f = get_fundamentals(ticker)
            if new_f:
                new_row = pd.DataFrame([new_f]).set_index('ticker')
                universe_df = pd.concat([universe_df, new_row])
            else:
                print(f"Could not fetch fundamentals for {ticker}. Skipping.")
                return None

        # 1. Get Event window
        stock_df = get_event_window(ticker, event_date)
        if stock_df.empty:
            print(f"No price data for {ticker}. Skipping.")
            return None

        # 2. Find Twins (excluding index members at the time of the event)
        index_tickers = get_index_tickers_at_date(event_date, index_type=index_type, current_tickers=current_index)
        twins = find_twins(ticker, universe_df, exclude_tickers=index_tickers)
        twin_tickers = twins.index.tolist()

        # 3. Build Twin Portfolio
        event_dt = pd.to_datetime(event_date)
        start = event_dt - pd.Timedelta(days=250*2)
        end = event_dt + pd.Timedelta(days=500*2)
        twin_portfolio = build_twin_portfolio(twin_tickers, start, end)
        if twin_portfolio.empty: return None

        # 4. Calculate Advanced Components
        # Find position of event_dt
        if event_dt not in stock_df.index:
            idx = stock_df.index.get_indexer([event_dt], method='nearest')[0]
            event_dt_actual = stock_df.index[idx]
        else:
            event_dt_actual = event_dt

        event_pos = stock_df.index.get_loc(event_dt_actual)

        # Liquidity Change (Volume expansion after inclusion)
        pre_vol = stock_df['Volume'].iloc[max(0, event_pos-30):event_pos].mean()
        post_vol = stock_df['Volume'].iloc[event_pos:min(len(stock_df), event_pos+30)].mean()
        liquidity_change = (post_vol / pre_vol - 1) if pre_vol > 0 else 0

        # Momentum Persistence
        pre_ret = stock_df['Close'].iloc[event_pos] / stock_df['Close'].iloc[max(0, event_pos-90)] - 1
        post_ret = stock_df['Close'].iloc[min(len(stock_df)-1, event_pos+90)] / stock_df['Close'].iloc[event_pos] - 1
        momentum_persistence = post_ret if pre_ret > 0 else 0 # Simplified logic

        # Valuation Expansion (Approximate using price if historical P/E unavailable)
        valuation_change = stock_df['Close'].iloc[min(len(stock_df)-1, event_pos+180)] / stock_df['Close'].iloc[event_pos] - 1

        # 5. Calculate Returns for Green Score
        common_index = stock_df.index.intersection(twin_portfolio.index)
        # Normalize returns from the event date onwards
        stock_subset = stock_df.loc[common_index]
        twin_subset = twin_portfolio.loc[common_index]

        # Get position of event in common index
        if event_dt_actual not in common_index:
            idx = common_index.get_indexer([event_dt_actual], method='nearest')[0]
            event_dt_common = common_index[idx]
        else:
            event_dt_common = event_dt_actual

        # Cumulative return from inclusion to end of window (+1 year approx)
        stock_final_ret = stock_subset['Close'].iloc[-1] / stock_subset['Close'].loc[event_dt_common]
        twin_final_ret = twin_subset.iloc[-1] / twin_subset.loc[event_dt_common]

        green_score = calculate_green_score(
            stock_final_ret,
            twin_final_ret,
            valuation_change=valuation_change,
            liquidity_change=liquidity_change,
            momentum_persistence=momentum_persistence
        )

        return {
            "ticker": ticker,
            "event_date": event_date,
            "green_score": green_score,
            "return_premium": stock_final_ret - twin_final_ret,
            "liquidity_impact": liquidity_change,
            "momentum_impact": momentum_persistence
        }
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None
