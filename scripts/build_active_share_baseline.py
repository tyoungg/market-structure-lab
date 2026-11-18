#!/usr/bin/env python3
"""Reproducible, source-separated Active Share baseline audit.

Usage:
  python scripts/build_active_share_baseline.py --tr path/to/TR.csv --crsp path/to/CRSP.csv --out data/processed

Raw inputs are never modified. Outputs are generated independently by provider.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

BENCHMARKS = {"S&P 500": ["as_S5", "as_s5", "S5", "as_sp500"],
               "Russell 1000": ["as_R1", "as_r1", "R1", "as_russell1000"]}
DATE_CANDIDATES = ["ym", "date", "year_month", "month"]
FUND_CANDIDATES = ["fundno", "crsp_portno", "wficn", "fund_id"]
ASSET_CANDIDATES = ["total_assets", "assets", "tna", "fund_assets"]

def column(df, candidates, required=True):
    lookup = {str(c).strip().lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lookup:
            return lookup[c.lower()]
    if required:
        raise ValueError(f"Required column not found. Tried {candidates}; available={list(df.columns)}")
    return None

def parse_date(s):
    # ND ym values are usually YYYYmM or numeric YYYYMM.
    raw = s.astype(str).str.strip().str.replace(".0", "", regex=False)
    # Handle strings such as 1979m6 explicitly (zero-pad month) and YYYYMM.
    ym = raw.str.extract(r"^(\\d{4})[mM]?(\\d{1,2})$")
    normalized = ym[0] + ym[1].str.zfill(2)
    parsed = pd.to_datetime(normalized, format="%Y%m", errors="coerce")
    if parsed.isna().any():
        fallback = pd.to_datetime(s, errors="coerce")
        parsed = parsed.fillna(fallback)
    if parsed.isna().all():
        raise ValueError("Could not parse date column; inspect ym values and update date parser.")
    return parsed

def read_source(path, provider):
    path = Path(path)
    df = pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_stata(path) if path.suffix.lower() == ".dta" else pd.read_parquet(path)
    date_col = column(df, DATE_CANDIDATES)
    fund_col = column(df, FUND_CANDIDATES)
    assets_col = column(df, ASSET_CANDIDATES, required=False)
    df["_date"] = parse_date(df[date_col])
    df["_year"] = df["_date"].dt.year
    df["_fund"] = df[fund_col].astype(str)
    if assets_col:
        df["_assets"] = pd.to_numeric(df[assets_col], errors="coerce")
    else:
        df["_assets"] = float("nan")
    for label, candidates in BENCHMARKS.items():
        c = column(df, candidates, required=False)
        if c:
            df[label] = pd.to_numeric(df[c], errors="coerce")
            # Active Share is conventionally percentage-valued; preserve original units.
    df["_provider"] = provider
    return df

def summarize(df, provider):
    rows=[]
    for year, group in df.groupby("_year", dropna=True):
        for benchmark in BENCHMARKS:
            if benchmark not in group:
                continue
            x = group[benchmark].dropna()
            if x.empty:
                continue
            assets = group.loc[x.index, "_assets"]
            w = assets.where(assets.gt(0))
            weighted = (x*w).sum()/w.sum() if w.notna().any() and w.sum()>0 else float("nan")
            rows.append({"provider":provider,"year":int(year),"benchmark":benchmark,
                "observations":int(x.count()),"unique_funds":int(group.loc[x.index,"_fund"].nunique()),
                "mean":x.mean(),"median":x.median(),"p10":x.quantile(.10),"p25":x.quantile(.25),
                "p75":x.quantile(.75),"p90":x.quantile(.90),"asset_weighted_mean":weighted,
                "assets_available_for_weighting":int(w.notna().sum())})
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tr", required=True, help="TR CSV/DTA/Parquet file")
    ap.add_argument("--crsp", required=True, help="CRSP CSV/DTA/Parquet file")
    ap.add_argument("--out", default="data/processed")
    args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    audits=[]; summaries=[]
    for provider, path in [("TR",args.tr),("CRSP",args.crsp)]:
        df=read_source(path,provider)
        audit={"provider":provider,"input_file":Path(path).name,"rows":len(df),"columns":len(df.columns),
            "duplicate_rows":int(df.duplicated().sum()),"missing_cells":int(df.isna().sum().sum()),
            "date_min":df["_date"].min(),"date_max":df["_date"].max(),"fund_id_column":column(df,FUND_CANDIDATES),
            "date_column":column(df,DATE_CANDIDATES),"assets_column":column(df,ASSET_CANDIDATES,False),
            "benchmark_columns_present":";".join([b for b in BENCHMARKS if b in df])}
        audits.append(audit)
        summaries.append(summarize(df,provider))
        df.drop(columns=["_date","_year","_fund","_assets","_provider"],errors="ignore").to_csv(out/f"{provider.lower()}_cleaned_source.csv",index=False)
    pd.DataFrame(audits).to_csv(out/"source_audit.csv",index=False)
    pd.concat(summaries,ignore_index=True).to_csv(out/"annual_baseline_summary.csv",index=False)
    print(pd.DataFrame(audits).to_string(index=False))
    print(f"Wrote source audit and annual summary to {out.resolve()}")
if __name__ == "__main__":
    main()
