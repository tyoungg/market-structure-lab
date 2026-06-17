import pandas as pd
from .price_data import load_price_history

def build_twin_portfolio(twin_tickers, start_date, end_date):
    """
    Builds an equal-weighted portfolio of the provided twin tickers.
    """
    prices = {}
    for ticker in twin_tickers:
        try:
            df = load_price_history(ticker, start=start_date, end=end_date)
            if not df.empty:
                prices[ticker] = df["Close"]
        except Exception as e:
            print(f"Error loading {ticker}: {e}")

    if not prices:
        return pd.Series()

    price_df = pd.DataFrame(prices)
    if price_df.empty:
        return pd.Series()

    price_df = price_df.dropna()

    # Handle multi-index if present (sometimes happens with yfinance download)
    if isinstance(price_df.columns, pd.MultiIndex):
        price_df.columns = price_df.columns.get_level_values(0)

    # Calculate returns normalized to 1.0 at start
    returns = price_df.div(price_df.iloc[0])

    # Equal weight mean
    portfolio = returns.mean(axis=1)

    return portfolio

def build_equal_weight_portfolio(tickers, start_date, end_date):
    """
    Generic function to build an equal-weight portfolio.
    """
    return build_twin_portfolio(tickers, start_date, end_date)

def compare_stock_to_twins(stock_ticker, twin_tickers, start_date, end_date):
    """
    Returns a comparison DataFrame between a stock and its twin portfolio.
    """
    stock_df = load_price_history(stock_ticker, start=start_date, end=end_date)
    twin_portfolio = build_twin_portfolio(twin_tickers, start_date, end_date)

    if stock_df.empty or twin_portfolio.empty:
        return pd.DataFrame()

    common_index = stock_df.index.intersection(twin_portfolio.index)

    stock_norm = stock_df.loc[common_index, "Close"] / stock_df.loc[common_index, "Close"].iloc[0]

    comparison_df = pd.DataFrame({
        "date": common_index,
        "stock_return": stock_norm.values,
        "twin_return": twin_portfolio.loc[common_index].values
    }).set_index("date")

    return comparison_df
