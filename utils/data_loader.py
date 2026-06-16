import pandas as pd
import os

DATA_DIR = "data"

def load_sp500_changes():
    """
    Loads S&P 500 inclusion/exclusion data.
    """
    path = os.path.join(DATA_DIR, "sp500_changes.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

def load_dow_changes():
    """
    Loads Dow Jones index change data.
    """
    path = os.path.join(DATA_DIR, "dow_changes.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return None
