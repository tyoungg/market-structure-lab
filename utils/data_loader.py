import pandas as pd
import os
import requests
from io import StringIO
import re

DATA_DIR = "data"

def load_sp500_changes():
    path = os.path.join(DATA_DIR, "sp500_changes.csv")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if 'event_date' in df.columns:
                df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')
                df = df.dropna(subset=['event_date'])
            return df
        except: return None
    return None

def load_dow_changes():
    path = os.path.join(DATA_DIR, "dow_changes.csv")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if 'event_date' in df.columns:
                df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')
                df = df.dropna(subset=['event_date'])
            return df
        except: return None
    return None

def extract_ticker(text):
    if pd.isna(text): return None
    text = str(text)
    match = re.search(r'\(([^)]+)\)', text)
    if match:
        ticker = match.group(1).split(':')[-1].strip()
        return ticker.split(' ')[0]
    words = text.split(' ')
    for w in reversed(words):
        w_clean = re.sub(r'[^A-Z.-]', '', w)
        if 1 <= len(w_clean) <= 5 and w_clean.isupper():
            return w_clean
    return words[0]

def normalize_index_changes(tables):
    for t in tables:
        if t.shape[1] < 2: continue

        # Flatten MultiIndex
        if isinstance(t.columns, pd.MultiIndex):
            new_cols = []
            for col in t.columns:
                c0, c1 = str(col[0]), str(col[1])
                if 'Added' in c0 and 'Ticker' in c1: new_cols.append('added_ticker')
                elif 'Removed' in c0 and 'Ticker' in c1: new_cols.append('removed_ticker')
                elif 'Date' in c0 or 'Date' in c1: new_cols.append('event_date')
                else: new_cols.append(c1)
            t.columns = new_cols

        mapping = {}
        for c in t.columns:
            cl = str(c).lower()
            if 'date' in cl: mapping[c] = 'event_date'
            elif 'added' in cl or 'addition' in cl or 'member added' in cl: mapping[c] = 'added_ticker'
            elif 'removed' in cl or 'removal' in cl or 'member removed' in cl: mapping[c] = 'removed_ticker'
            elif 'ticker' in cl or 'symbol' in cl:
                if 'added_ticker' not in mapping.values(): mapping[c] = 'added_ticker'
                elif 'removed_ticker' not in mapping.values(): mapping[c] = 'removed_ticker'

        t = t.rename(columns=mapping)
        if 'event_date' in t.columns and ('added_ticker' in t.columns or 'removed_ticker' in t.columns):
            df = t.copy()
            df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')
            df = df.dropna(subset=['event_date'])
            for col in ['added_ticker', 'removed_ticker']:
                if col in df.columns:
                    df[col] = df[col].apply(extract_ticker)
                else:
                    df[col] = None
            return df[['event_date', 'added_ticker', 'removed_ticker']]
    return None

def update_sp500_changes():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))
        df = normalize_index_changes(tables)
        if df is not None:
            os.makedirs(DATA_DIR, exist_ok=True)
            df.to_csv(os.path.join(DATA_DIR, "sp500_changes.csv"), index=False)
            return df
    except Exception as e:
        print(f"Error updating S&P 500 changes: {e}")
    return None

def update_dow_changes():
    url = 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))
        df = normalize_index_changes(tables)

        if df is None:
            url_hist = 'https://en.wikipedia.org/wiki/Historical_components_of_the_Dow_Jones_Industrial_Average'
            response = requests.get(url_hist, headers=headers)
            tables = pd.read_html(StringIO(response.text))
            df = normalize_index_changes(tables)

        if df is not None:
            os.makedirs(DATA_DIR, exist_ok=True)
            df.to_csv(os.path.join(DATA_DIR, "dow_changes.csv"), index=False)
            return df
    except Exception as e:
        print(f"Error updating Dow changes: {e}")
    return None

def get_index_additions(index_type='sp500'):
    df = load_sp500_changes() if index_type == 'sp500' else load_dow_changes()
    if df is None: return []
    additions = df[df['added_ticker'].notnull()].copy()
    return list(zip(additions['added_ticker'], additions['event_date']))

def get_current_sp500_constituents(refresh=False):
    path = os.path.join(DATA_DIR, "sp500_constituents.csv")
    if not refresh and os.path.exists(path):
        try:
            return set(pd.read_csv(path)['Symbol'].tolist())
        except: pass

    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))
        current_df = tables[0]
        if isinstance(current_df.columns, pd.MultiIndex):
            current_df.columns = current_df.columns.get_level_values(-1)
        symbol_col = next((c for c in current_df.columns if 'Symbol' in c or 'Ticker' in c), None)
        if symbol_col:
            tickers = current_df[symbol_col].apply(lambda x: str(x).replace('.', '-')).tolist()
            # Cache it
            pd.DataFrame({'Symbol': tickers}).to_csv(path, index=False)
            return set(tickers)
    except: pass
    return set()

def get_current_dow_constituents(refresh=False):
    path = os.path.join(DATA_DIR, "dow_constituents.csv")
    if not refresh and os.path.exists(path):
        try:
            return set(pd.read_csv(path)['Symbol'].tolist())
        except: pass

    url = 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(response.text))
        for t in tables:
            if 'Symbol' in t.columns:
                tickers = t['Symbol'].apply(lambda x: str(x).replace('.', '-')).tolist()
                # Cache it
                pd.DataFrame({'Symbol': tickers}).to_csv(path, index=False)
                return set(tickers)
    except: pass
    return set()

def get_index_tickers_at_date(target_date, index_type='sp500', current_tickers=None):
    target_date = pd.to_datetime(target_date)
    if current_tickers is None:
        current_tickers = get_current_sp500_constituents() if index_type == 'sp500' else get_current_dow_constituents()

    changes_df = load_sp500_changes() if index_type == 'sp500' else load_dow_changes()
    if changes_df is None: return current_tickers

    changes_df = changes_df.sort_values('event_date', ascending=False)
    history_tickers = current_tickers.copy()
    for _, row in changes_df.iterrows():
        if row['event_date'] > target_date:
            if pd.notnull(row['added_ticker']): history_tickers.discard(row['added_ticker'])
            if pd.notnull(row['removed_ticker']): history_tickers.add(row['removed_ticker'])
        else: break
    return history_tickers

def get_all_historical_tickers(index_type='both'):
    """
    Returns a set of all tickers that have ever been in the index (based on CSVs).
    """
    tickers = set()

    if index_type in ['sp500', 'both']:
        tickers.update(get_current_sp500_constituents())
        df = load_sp500_changes()
        if df is not None:
            tickers.update(df['added_ticker'].dropna().tolist())
            tickers.update(df['removed_ticker'].dropna().tolist())

    if index_type in ['dow', 'both']:
        tickers.update(get_current_dow_constituents())
        df = load_dow_changes()
        if df is not None:
            tickers.update(df['added_ticker'].dropna().tolist())
            tickers.update(df['removed_ticker'].dropna().tolist())

    return sorted(list(tickers))
