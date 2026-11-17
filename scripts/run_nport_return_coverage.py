#!/usr/bin/env python3
"""Run the AB May/June 2026 no-trade return-coverage pilot from audited N-PORT extracts.

The three compact input CSVs are extracted from SEC 2026 Q3 N-PORT tables.
IVV's benchmark vector is compressed only outside the union of AB's May and
June holdings; this preserves Active Share against both AB portfolios exactly.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from run_nport_pilot import active_share, calculate_no_trade, fetch_returns

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "nport_pilot_inputs"


def read_weights(path: Path, label: str) -> pd.DataFrame:
    x = pd.read_csv(path, dtype={"SECURITY_KEY": str, "ISIN": str, "ISSUER_CUSIP": str})
    required = {"SECURITY_KEY", "ISIN", "ISSUER_CUSIP", "ISSUER_NAME", "EQUITY_WEIGHT"}
    missing = required - set(x.columns)
    if missing:
        raise ValueError(f"{label}: missing columns {sorted(missing)}")
    if x.SECURITY_KEY.isna().any() or x.SECURITY_KEY.duplicated().any():
        raise ValueError(f"{label}: security keys must be present and unique")
    x["EQUITY_WEIGHT"] = pd.to_numeric(x.EQUITY_WEIGHT, errors="raise")
    if (x.EQUITY_WEIGHT < 0).any():
        raise ValueError(f"{label}: negative equity weight found")
    total = float(x.EQUITY_WEIGHT.sum())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"{label}: weights sum to {total:.12f}, expected 1.0")
    return x


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--start-date", default="2026-05-31")
    p.add_argument("--end-date", default="2026-06-30")
    p.add_argument("--output-dir", type=Path, default=Path("data/nport_pilot_returns"))
    a = p.parse_args()
    a.output_dir.mkdir(parents=True, exist_ok=True)

    start = read_weights(a.input_dir / "ab_may_2026_equity.csv", "AB May start")
    actual = read_weights(a.input_dir / "ab_june_2026_equity.csv", "AB June actual")
    benchmark = read_weights(a.input_dir / "ivv_june_2026_compact_equity.csv", "IVV June benchmark")

    returns = fetch_returns(start, a.start_date, a.end_date)
    returns.to_csv(a.output_dir / "security_returns.csv", index=False)

    return_columns = ["SECURITY_KEY", "RETURN", "TICKER_RESOLVED"] + [
        col for col in ("FIGI_CANDIDATES", "MAPPING_ERROR") if col in returns.columns
    ]
    diagnostic = start.merge(
        returns[return_columns],
        on="SECURITY_KEY", how="left", validate="one_to_one"
    )
    diagnostic["COVERAGE_STATUS"] = "RETURN_AVAILABLE"
    diagnostic.loc[diagnostic.TICKER_RESOLVED.fillna("").eq(""), "COVERAGE_STATUS"] = "NO_TICKER_MAPPING"
    diagnostic.loc[
        diagnostic.TICKER_RESOLVED.fillna("").ne("") & diagnostic.RETURN.isna(),
        "COVERAGE_STATUS"
    ] = "NO_PRICE_ON_REQUIRED_DATES"
    diagnostic.to_csv(a.output_dir / "starting_position_coverage.csv", index=False)

    no_trade, coverage = calculate_no_trade(start, returns)
    actual_as = active_share(actual, benchmark)
    summary = {
        "fund": "AB Large Cap Value Fund",
        "benchmark": "iShares Core S&P 500 ETF (IVV) N-PORT holdings proxy",
        "start_report_date": a.start_date,
        "end_report_date": a.end_date,
        "start_positions": int(len(start)),
        "positions_with_ticker_mapping": int(diagnostic.TICKER_RESOLVED.fillna("").ne("").sum()),
        "weight_with_ticker_mapping": float(diagnostic.loc[diagnostic.TICKER_RESOLVED.fillna("").ne(""), "EQUITY_WEIGHT"].sum()),
        "positions_with_valid_adjusted_return": int(diagnostic.RETURN.notna().sum()),
        "return_coverage_start_equity_weight": float(coverage),
        "uncovered_start_equity_weight": float(1.0 - coverage),
        "uncovered_start_positions": diagnostic.loc[
            diagnostic.RETURN.isna(),
            ["SECURITY_KEY", "ISSUER_NAME", "EQUITY_WEIGHT", "TICKER_RESOLVED",
             "COVERAGE_STATUS"] + [col for col in ("FIGI_CANDIDATES", "MAPPING_ERROR") if col in diagnostic.columns]
        ].to_dict(orient="records"),
        "actual_end_active_share_vs_ivv_proxy": float(actual_as),
        "strict_no_trade_estimate_calculated": bool(no_trade is not None),
        "no_trade_active_share_vs_ivv_proxy": None,
        "actual_minus_no_trade_active_share": None,
        "interpretation": None,
        "price_source": "Yahoo Finance auto-adjusted daily Close",
        "identifier_source": "OpenFIGI v3 mapping API (ISIN first; CUSIP fallback)",
        "price_date_rule": "Last SPY trading date on or before each N-PORT report date; no stale-price carry-forward",
        "limitations": [
            "This is a one-interval equity-sleeve feasibility estimate, not a causal estimate.",
            "Yahoo adjusted prices and OpenFIGI mappings are public feasibility sources, not a complete institutional security master.",
            "A missing return blocks the strict no-trade result; no subset renormalization is used.",
            "Foreign issuers, delistings, mergers, ticker changes and corporate actions require position-level review.",
            "Cash and derivatives are excluded from the normalized equity-sleeve calculation.",
            "IVV is an S&P 500 tracker-fund holdings proxy, not official index weights.",
        ],
    }
    if no_trade is not None:
        nt_as = active_share(no_trade, benchmark)
        delta = actual_as - nt_as
        summary["no_trade_active_share_vs_ivv_proxy"] = float(nt_as)
        summary["actual_minus_no_trade_active_share"] = float(delta)
        summary["interpretation"] = (
            "Negative: actual trading moved the equity sleeve closer to IVV than no-trade drift; "
            "positive: actual trading moved it farther away."
        )
        no_trade.to_csv(a.output_dir / "no_trade_end_equity_weights.csv", index=False)
    else:
        summary["interpretation"] = (
            "Strict no-trade Active Share withheld because beginning equity-weight return coverage is below 100%."
        )

    (a.output_dir / "pilot_return_coverage_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
