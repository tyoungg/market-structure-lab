"""Validated, source-separated loaders for the Rational Coward dashboard."""
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "public_active_share"


def available_files():
    if not DATA_DIR.exists():
        return []
    return sorted([*DATA_DIR.glob("*.csv"), *DATA_DIR.glob("*.parquet"), *DATA_DIR.glob("*.pq")])


def load_dataset(path: Path):
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_parquet(path)



def audit_dataset(df: pd.DataFrame):
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_cells": int(df.isna().sum().sum()),
        "column_names": list(map(str, df.columns)),
    }


def find_column(df: pd.DataFrame, candidates):
    normalized = {str(c).strip().lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]
    return None
