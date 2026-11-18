#!/usr/bin/env python3
"""Reproducible descriptive Active Share baseline; TR and CRSP remain separate.

Raw source files are read-only and are never copied into the repository.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import pandas as pd

BENCHMARKS = {
    "S&P 500": "as_s5",
    "Russell 1000": "as_r1",
}
ID_COLUMNS = {"TR": "fundno", "CRSP": "crsp_portno"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_ym(values: pd.Series) -> pd.Series:
    raw = values.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    parts = raw.str.extract(r"^(\d{4})[mM]?(\d{1,2})$")
    month = pd.to_numeric(parts[1], errors="coerce")
    valid = month.between(1, 12)
    normalized = parts[0] + month.where(valid).astype("Int64").astype("string").str.zfill(2)
    parsed = pd.to_datetime(normalized, format="%Y%m", errors="coerce")
    # Do not silently reinterpret malformed values using a permissive parser.
    return parsed


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def audit_provider(provider: str, path: Path, out: Path) -> tuple[dict, pd.DataFrame]:
    df = read_csv(path)
    id_col = ID_COLUMNS[provider]
    required = [id_col, "ym", "total_assets", *BENCHMARKS.values()]
    missing_columns = [c for c in required if c not in df.columns]
    if missing_columns:
        raise ValueError(f"{provider}: required columns missing: {missing_columns}")

    dates = parse_ym(df["ym"])
    assets = pd.to_numeric(df["total_assets"], errors="coerce")
    benchmark_data = {label: pd.to_numeric(df[col], errors="coerce")
                      for label, col in BENCHMARKS.items()}
    date_fail = int(dates.isna().sum())
    if date_fail:
        examples = df.loc[dates.isna(), "ym"].astype(str).head(10).tolist()
        raise ValueError(f"{provider}: {date_fail} unparseable ym values; examples={examples}")

    # Tiny negative values at approximately machine precision are retained in source,
    # but flagged separately from economically meaningful out-of-range values.
    benchmark_checks = {}
    for label, values in benchmark_data.items():
        benchmark_checks[label] = {
            "missing": int(values.isna().sum()),
            "min": float(values.min()),
            "max": float(values.max()),
            "outside_0_1_tolerance": int(((values < -1e-6) | (values > 1 + 1e-6)).sum()),
            "tiny_rounding_deviations": int(((values < 0) | (values > 1)) .sum()),
        }

    key_dupes = int(df.duplicated([id_col, "ym"]).sum())
    if key_dupes:
        raise ValueError(f"{provider}: {key_dupes} duplicate {id_col}/ym keys")

    annual_rows = []
    year = dates.dt.year
    for yr in sorted(year.unique()):
        mask = year.eq(yr)
        for label, values in benchmark_data.items():
            x = values.loc[mask]
            valid = x.notna()
            x = x.loc[valid]
            if x.empty:
                continue
            w = assets.loc[x.index].where(assets.loc[x.index].gt(0))
            weighted_mean = float((x * w).sum() / w.sum()) if w.notna().any() and w.sum() > 0 else None
            annual_rows.append({
                "provider": provider, "year": int(yr), "benchmark": label,
                "observations": int(x.count()),
                "unique_funds": int(df.loc[x.index, id_col].nunique()),
                "mean": float(x.mean()), "median": float(x.median()),
                "p10": float(x.quantile(.10)), "p25": float(x.quantile(.25)),
                "p75": float(x.quantile(.75)), "p90": float(x.quantile(.90)),
                "asset_weighted_mean": weighted_mean,
                "assets_available_for_weighting": int(w.notna().sum()),
            })

    audit = {
        "provider": provider, "source_file": path.name, "source_bytes": path.stat().st_size,
        "source_sha256": sha256_file(path), "rows": int(len(df)), "columns": int(len(df.columns)),
        "column_names": "|".join(df.columns.astype(str)),
        "date_column": "ym", "date_parse_failures": date_fail,
        "date_min": dates.min().strftime("%Y-%m-%d"), "date_max": dates.max().strftime("%Y-%m-%d"),
        "distinct_periods": int(dates.nunique()), "fund_id_column": id_col,
        "unique_fund_ids": int(df[id_col].nunique()), "missing_fund_ids": int(df[id_col].isna().sum()),
        "duplicate_fund_period_keys": key_dupes, "duplicate_full_rows": int(df.duplicated().sum()),
        "missing_wficn": int(df["wficn"].isna().sum()) if "wficn" in df else None,
        "missing_assets": int(assets.isna().sum()), "nonpositive_assets": int((assets <= 0).sum()),
        "benchmark_checks_json": pd.Series(benchmark_checks).to_json(),
    }
    return audit, pd.DataFrame(annual_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tr", required=True, type=Path)
    parser.add_argument("--crsp", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    audits, summaries = [], []
    for provider, path in (("TR", args.tr), ("CRSP", args.crsp)):
        audit, summary = audit_provider(provider, path, args.out)
        audits.append(audit)
        summaries.append(summary)

    pd.DataFrame(audits).to_csv(args.out / "source_audit.csv", index=False)
    pd.concat(summaries, ignore_index=True).to_csv(args.out / "annual_baseline_summary.csv", index=False)
    print(pd.DataFrame(audits)[["provider", "rows", "date_min", "date_max",
          "distinct_periods", "unique_fund_ids", "duplicate_fund_period_keys"]].to_string(index=False))
    print(f"Outputs written to {args.out}")


if __name__ == "__main__":
    main()
