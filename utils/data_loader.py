import pandas as pd
import os
import requests
from io import StringIO

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
        tables = pd.read_html(StringIO(response.text))

        df = None
        for t in tables:
            if isinstance(t.columns, pd.MultiIndex):
                # Flatten the MultiIndex manually to avoid name collisions before renaming
                # Table 1: ('Added', 'Ticker'), ('Removed', 'Ticker')
                new_cols = []
                for col in t.columns:
                    if col[0] == 'Added' and col[1] == 'Ticker':
                        new_cols.append('Added')
                    elif col[0] == 'Removed' and col[1] == 'Ticker':
                        new_cols.append('Removed')
                    elif 'Date' in col[0] or 'Date' in col[1]:
                        new_cols.append('Date')
                    else:
                        new_cols.append(col[1])
                t.columns = new_cols
                actual_cols = t.columns
            else:
                actual_cols = t.columns

            # Robust header detection
            cols_str = [str(c) for c in actual_cols]
            if (any('Added' in c for c in cols_str) or any('Ticker' in c for c in cols_str)) and any('Date' in c for c in cols_str):
                df = t
                break

        if df is not None:
            if not os.path.exists(DATA_DIR):
                os.makedirs(DATA_DIR)
            path = os.path.join(DATA_DIR, "sp500_changes.csv")
            df.to_csv(path, index=False)
            return df
    except Exception as e:
        print(f"Error updating S&P 500 changes: {e}")
        import traceback
        traceback.print_exc()
    return None

def update_dow_changes():
    """
    Scrapes historical Dow Jones changes from Wikipedia.
    """
    url = 'https://en.wikipedia.org/wiki/Historical_components_of_the_Dow_Jones_Industrial_Average'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))

        all_changes = []
        for t in tables:
            if isinstance(t.columns, pd.MultiIndex):
                t.columns = t.columns.get_level_values(-1)

            cols = [str(c) for c in t.columns]
            # Dow page has many small tables for changes
            if any('Added' in c for c in cols) or any('Removed' in c for c in cols):
                # Standardize columns
                t = t.copy()
                t.columns = [str(c) for c in t.columns]

                # Rename for consistency if needed
                mapping = {
                    'Member added': 'Added',
                    'Member removed': 'Removed',
                    'Addition': 'Added',
                    'Removal': 'Removed'
                }
                t = t.rename(columns=mapping)
                all_changes.append(t)

        if all_changes:
            df = pd.concat(all_changes, ignore_index=True)
            # Normalize dates
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.dropna(subset=['Date'])

            path = os.path.join(DATA_DIR, "dow_changes.csv")
            df.to_csv(path, index=False)
            return df

    except Exception as e:
        print(f"Error updating Dow changes: {e}")
    return None

def get_index_additions(index_type='sp500'):
    """
    Returns a list of (ticker, date) tuples for additions.
    """
    if index_type == 'sp500':
        df = load_sp500_changes()
    else:
        df = load_dow_changes()

    if df is None:
        return []

    date_col = next((c for c in df.columns if 'Date' in c), None)
    ticker_col = next((c for c in df.columns if 'Added' in c or 'Ticker' in c or 'Symbol' in c), None)

    if not date_col or not ticker_col:
        return []

    additions = df[df[ticker_col].notnull()].copy()
    additions[date_col] = pd.to_datetime(additions[date_col], errors='coerce')
    additions = additions.dropna(subset=[date_col])
    additions = additions.sort_values(date_col, ascending=False)

    return list(zip(additions[ticker_col], additions[date_col]))

def get_current_sp500_constituents():
    """
    Fetches the current S&P 500 constituents.
    """
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))
        current_df = tables[0]
        if isinstance(current_df.columns, pd.MultiIndex):
            current_df.columns = current_df.columns.get_level_values(-1)
        symbol_col = next((c for c in current_df.columns if 'Symbol' in c or 'Ticker' in c), None)
        if symbol_col:
            return set(current_df[symbol_col].apply(lambda x: str(x).replace('.', '-')).tolist())
    except Exception as e:
        print(f"Error fetching current S&P 500 constituents: {e}")
    return set()

def get_current_dow_constituents():
    """
    Fetches the current Dow Jones constituents.
    """
    url = 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))
        for t in tables:
            if 'Symbol' in t.columns:
                return set(t['Symbol'].apply(lambda x: str(x).replace('.', '-')).tolist())
    except Exception as e:
        print(f"Error fetching current Dow constituents: {e}")
    return set()

def get_index_tickers_at_date(target_date, index_type='sp500', current_tickers=None):
    """
    Computes index members on a specific historical date with fallback.
    """
    target_date = pd.to_datetime(target_date)

    if current_tickers is None:
        if index_type == 'sp500':
            current_tickers = get_current_sp500_constituents()
        else:
            current_tickers = get_current_dow_constituents()

    if index_type == 'sp500':
        changes_df = load_sp500_changes()
    else:
        changes_df = load_dow_changes()

    if changes_df is None:
        return current_tickers

    date_col = next((c for c in changes_df.columns if 'Date' in c), 'Date')
    added_col = next((c for c in changes_df.columns if 'Added' in c), 'Added')
    removed_col = next((c for c in changes_df.columns if 'Removed' in c), 'Removed')

    if date_col not in changes_df.columns:
        return current_tickers

    changes_df[date_col] = pd.to_datetime(changes_df[date_col], errors='coerce')
    changes_df = changes_df.dropna(subset=[date_col])
    changes_df = changes_df.sort_values(date_col, ascending=False)

    history_tickers = current_tickers.copy()
    for _, row in changes_df.iterrows():
        if row[date_col] <= target_date:
            break
        if added_col in row and pd.notnull(row[added_col]):
            history_tickers.discard(str(row[added_col]).split(' ')[0])
        if removed_col in row and pd.notnull(row[removed_col]):
            history_tickers.add(str(row[removed_col]).split(' ')[0])

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
    Returns a set of all known index tickers.
    """
    tickers = set()
    sp_df = load_sp500_changes()
    if sp_df is not None and 'Added' in sp_df.columns:
        tickers.update(sp_df['Added'].dropna().apply(lambda x: str(x).split(' ')[0]).unique())
    dow_df = load_dow_changes()
    if dow_df is not None and 'Added' in dow_df.columns:
        tickers.update(dow_df['Added'].dropna().apply(lambda x: str(x).split(' ')[0]).unique())
    return tickers
