import pandas as pd
import os
import requests

DATA_DIR = "data"

def load_sp500_changes():
    """
    Loads S&P 500 inclusion/exclusion data.
    """
    path = os.path.join(DATA_DIR, "sp500_changes.csv")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.dropna(subset=['Date'])
            return df
        except:
            return None
    return None

def update_sp500_changes():
    """
    Scrapes historical S&P 500 changes from Wikipedia.
    """
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(response.text)

        # Find the changes table - look for specific headers
        df = None
        for t in tables:
            if 'Added' in str(t.columns) and 'Removed' in str(t.columns):
                df = t
                break

        if df is None:
            # Fallback to the second table if header detection fails
            df = tables[1]

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(-1)

        path = os.path.join(DATA_DIR, "sp500_changes.csv")
        df.to_csv(path, index=False)
        return df
    except Exception as e:
        print(f"Error updating S&P 500 changes: {e}")
        return None

def get_sp500_additions():
    """
    Returns a list of (ticker, date) tuples for additions.
    """
    df = load_sp500_changes()
    if df is None or 'Added' not in df.columns:
        return []

    additions = df[df['Added'].notnull()]
    return list(zip(additions['Added'], additions['Date']))

def get_current_sp500_constituents():
    """
    Fetches the current S&P 500 constituents from Wikipedia.
    """
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(response.text)
        current_df = tables[0]

        if isinstance(current_df.columns, pd.MultiIndex):
            current_df.columns = current_df.columns.get_level_values(-1)

        symbol_col = next((c for c in current_df.columns if 'Symbol' in c or 'Ticker' in c), None)
        if symbol_col:
            return set(current_df[symbol_col].tolist())
    except Exception as e:
        print(f"Error fetching current constituents: {e}")
    return set()

def get_index_tickers_at_date(target_date, current_tickers=None):
    """
    Computes the set of index members on a specific historical date.
    """
    target_date = pd.to_datetime(target_date)

    # 1. Get current constituents
    if current_tickers is None:
        current_tickers = get_current_sp500_constituents()

    # 2. Get changes
    changes_df = load_sp500_changes()
    if changes_df is None:
        return current_tickers

    # 3. Work backwards from 'now' to target_date
    changes_df = changes_df.sort_values('Date', ascending=False)
    history_tickers = current_tickers.copy()

    for _, row in changes_df.iterrows():
        change_date = pd.to_datetime(row['Date'])
        if change_date <= target_date:
            break

        if pd.notnull(row['Added']):
            history_tickers.discard(row['Added'])
        if pd.notnull(row['Removed']):
            history_tickers.add(row['Removed'])

    return history_tickers

def load_dow_changes():
    """
    Loads Dow Jones index change data.
    """
    path = os.path.join(DATA_DIR, "dow_changes.csv")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.dropna(subset=['Date'])
            return df
        except:
            return None
    return None

def get_all_index_tickers():
    """
    Returns a set of all tickers that have EVER been part of the indexes in our record.
    """
    tickers = set()

    sp_df = load_sp500_changes()
    if sp_df is not None:
        if 'Added' in sp_df.columns:
            tickers.update(sp_df['Added'].dropna().unique())
        if 'Removed' in sp_df.columns:
            tickers.update(sp_df['Removed'].dropna().unique())

    dow_df = load_dow_changes()
    if dow_df is not None:
        if 'Added' in dow_df.columns:
            tickers.update(dow_df['Added'].dropna().unique())
        if 'Removed' in dow_df.columns:
            tickers.update(dow_df['Removed'].dropna().unique())

    return tickers
