from .event_study import run_event_analysis
from .data_loader import load_sp500_changes, load_dow_changes
from .fundamentals import load_fundamental_universe
import pandas as pd

def analyze_single_event(ticker, event_date):
    """
    Orchestrates the analysis of a single ticker event.
    """
    universe_df = load_fundamental_universe()
    if universe_df is None:
        return None

    return run_event_analysis(ticker, event_date, universe_df)

def analyze_sp500_additions():
    """
    Orchestrates the analysis of all S&P 500 additions in the dataset.
    """
    events_df = load_sp500_changes()
    if events_df is None or events_df.empty:
        return pd.DataFrame()

    universe_df = load_fundamental_universe()
    if universe_df is None:
        return pd.DataFrame()

    # Filter for additions only if the dataframe has an 'Added' column or similar
    # Assuming 'Added' column exists per the design doc
    results = []
    # If the CSV has 'Date' and 'Added' (ticker)
    for index, row in events_df.iterrows():
        if pd.notnull(row.get('Added')):
            res = run_event_analysis(row['Added'], row['Date'], universe_df)
            if res:
                results.append(res)

    return pd.DataFrame(results)

def analyze_dow_changes():
    """
    Orchestrates the analysis of all Dow Jones changes.
    """
    events_df = load_dow_changes()
    if events_df is None or events_df.empty:
        return pd.DataFrame()

    universe_df = load_fundamental_universe()
    if universe_df is None:
        return pd.DataFrame()

    results = []
    for index, row in events_df.iterrows():
        # Assuming Dow CSV structure
        ticker = row.get('Added') or row.get('ticker')
        date = row.get('Date') or row.get('event_date')
        if ticker and date:
            res = run_event_analysis(ticker, date, universe_df)
            if res:
                results.append(res)

    return pd.DataFrame(results)
