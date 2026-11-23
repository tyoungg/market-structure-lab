#!/usr/bin/env python3
"""Multi-fund C.2 no-trade drift and Active Share decomposition."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_c2_no_trade_drift_pilot import (  # noqa: E402
    END_DATE, MIN_PRICE_COVERAGE, START_DATE, active_share, decompose_active_share,
    download_total_returns, drift_weights, missing_return_sensitivity, security_identifier,
    write_csv,
)


def portfolio(holdings: pd.DataFrame, entity: str, date: str,
              ticker_by_security: dict[str, str]) -> tuple[dict, pd.DataFrame]:
    subset = holdings[
        holdings["entity"].eq(entity)
        & holdings["report_date"].eq(date)
        & holdings["is_common_equity"].astype(str).str.lower().eq("true")
    ].copy()
    if subset.empty:
        raise ValueError(f"No common-equity holdings for {entity} {date}")
    subset["weight_pct_nav_num"] = pd.to_numeric(subset["pct_net_assets"], errors="coerce").fillna(0.0)
    subset["security_id"] = subset.apply(lambda r: security_identifier(r.to_dict()), axis=1)
    rows = []
    for sid, group in subset.groupby("security_id", sort=True):
        rows.append({
            "entity": entity, "report_date": date, "security_id": sid,
            "name": next((str(x) for x in group["name"] if str(x).strip()), ""),
            "cusip": next((str(x) for x in group["cusip"] if str(x).strip()), ""),
            "isin": next((str(x) for x in group["isin"] if str(x).strip()), ""),
            "nport_ticker": "|".join(sorted({str(x).strip().upper() for x in group["ticker"] if str(x).strip()})),
            "mapped_ticker": ticker_by_security.get(sid, ""),
            "weight_pct_nav": float(group["weight_pct_nav_num"].sum()),
            "source_position_rows": int(len(group)),
        })
    result = pd.DataFrame(rows)
    equity_nav = float(result["weight_pct_nav"].sum())
    if equity_nav <= 0:
        raise ValueError(f"Non-positive common-equity weight for {entity} {date}")
    result["weight"] = result["weight_pct_nav"] / equity_nav
    result["weight_pct_equity"] = 100.0 * result["weight"]
    return {
        "entity": entity, "report_date": date, "equity_weight_pct_nav": equity_nav,
        "position_rows": int(len(subset)), "unique_securities": int(len(result)),
    }, result.sort_values("security_id").reset_index(drop=True)



def coverage_gate_pass(priced_weight_fraction: float, threshold: float = MIN_PRICE_COVERAGE) -> bool:
    return float(priced_weight_fraction) >= float(threshold)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="c2_nport_cohort")
    parser.add_argument("--out", default="c2_nport_cohort")
    parser.add_argument("--start-date", default=START_DATE)
    parser.add_argument("--end-date", default=END_DATE)
    args = parser.parse_args()
    source, out = Path(args.input), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    holdings = pd.read_csv(source / "nport_cohort_common_equity.csv", dtype=str).fillna("")
    mapping = pd.read_csv(source / "c2_security_identifier_map.csv", dtype=str).fillna("")
    mapping_coverage = pd.read_csv(source / "c2_identifier_mapping_coverage_by_entity.csv", dtype=str).fillna("")
    required = {"security_id", "mapped_ticker", "mapping_status"}
    if not required.issubset(mapping.columns):
        raise ValueError(f"Mapping file missing columns: {sorted(required - set(mapping.columns))}")
    if mapping["security_id"].duplicated().any():
        raise ValueError("Security mapping contains duplicate security_id rows")
    ticker_by_security = dict(zip(mapping["security_id"], mapping["mapped_ticker"].str.strip().str.upper()))

    entities = sorted(holdings.loc[holdings["report_date"].eq(args.start_date), "entity"].unique())
    roles = holdings.groupby("entity")["role"].first().to_dict()
    portfolios: dict[tuple[str, str], pd.DataFrame] = {}
    portfolio_meta = []
    for entity in entities:
        for date in (args.start_date, args.end_date):
            meta, frame = portfolio(holdings, entity, date, ticker_by_security)
            portfolios[(entity, date)] = frame
            portfolio_meta.append(meta)

    start_tickers = sorted({
        ticker for entity in entities
        for ticker in portfolios[(entity, args.start_date)]["mapped_ticker"].tolist() if ticker
    })
    ticker_isins = {}
    for entity in entities:
        frame = portfolios[(entity, args.start_date)]
        for row in frame.to_dict("records"):
            if row["mapped_ticker"] and row["isin"]:
                ticker_isins.setdefault(row["mapped_ticker"], row["isin"])
    prices, price_audit, yfinance_version = download_total_returns(
        start_tickers, ticker_isins, start_date=args.start_date, end_date=args.end_date
    )

    mapping_coverage_by_entity = {
        row["entity"]: float(row["ticker_mapping_coverage_pct_starting_equity"]) / 100.0
        for row in mapping_coverage.to_dict("records")
    }
    coverage_rows = []
    returns_by_entity: dict[str, dict[str, float]] = {}
    unpriced_by_entity: dict[str, list[str]] = {}
    price_rows = []
    for entity in entities:
        frame = portfolios[(entity, args.start_date)]
        returns, unpriced = {}, []
        priced_weight = 0.0
        for row in frame.to_dict("records"):
            sid, ticker, weight = row["security_id"], row["mapped_ticker"], float(row["weight"])
            price = prices.get(ticker) if ticker else None
            if price:
                ret = float(price["total_return"])
                priced_weight += weight
                status = price.get("status", "priced")
            else:
                ret, status = 0.0, "unpriced_zero_return_assumption"
                unpriced.append(sid)
            returns[sid] = ret
            price_rows.append({
                "entity": entity, "role": roles[entity], "security_id": sid,
                "name": row["name"], "mapped_ticker": ticker,
                "start_weight_pct_equity": 100.0 * weight,
                "total_return_pct": 100.0 * ret, "price_status": status,
                "yahoo_symbol": price.get("yahoo_symbol", "") if price else "",
                "quote_currency": price.get("quote_currency", "USD" if price and "." not in str(price.get("yahoo_symbol", "")) else "") if price else "",
                "local_total_return_pct": 100.0 * float(price.get("local_total_return", price.get("total_return", 0.0))) if price else "",
                "fx_symbol": price.get("fx_symbol", "") if price else "",
                "fx_start_rate": price.get("fx_start_rate", "") if price else "",
                "fx_end_rate": price.get("fx_end_rate", "") if price else "",
                "usd_conversion_status": price.get("usd_conversion_status", "not_required_usd_listing") if price else "",
                "start_adj_close": price.get("start_adj_close", "") if price else "",
                "end_adj_close": price.get("end_adj_close", "") if price else "",
            })
        coverage = priced_weight
        returns_by_entity[entity] = returns
        unpriced_by_entity[entity] = unpriced
        mapping_coverage_fraction = mapping_coverage_by_entity.get(entity, 0.0)
        coverage_rows.append({
            "entity": entity, "role": roles[entity],
            "ticker_mapping_coverage_pct_starting_equity": 100.0 * mapping_coverage_fraction,
            "mapping_coverage_gate_pass": coverage_gate_pass(mapping_coverage_fraction),
            "starting_unique_securities": int(len(frame)),
            "mapped_ticker_securities": int(frame["mapped_ticker"].ne("").sum()),
            "priced_starting_equity_weight_pct": 100.0 * priced_weight,
            "unpriced_starting_equity_weight_pct": 100.0 * (1.0 - priced_weight),
            "price_coverage_pct_starting_equity": 100.0 * coverage,
            "price_coverage_gate_pct": 100.0 * MIN_PRICE_COVERAGE,
            "price_gate_pass": coverage_gate_pass(coverage),
            "unpriced_security_count": len(unpriced),
        })

    coverage_by_entity = {x["entity"]: x for x in coverage_rows}
    fund_entities = [x for x in entities if roles[x] == "fund"]
    benchmark_entities = [x for x in entities if str(roles[x]).startswith("benchmark_")]
    decompositions, sensitivity_rows, drift_rows = [], [], []
    for fund in fund_entities:
        f0, f1 = portfolios[(fund, args.start_date)], portfolios[(fund, args.end_date)]
        start_weights = dict(zip(f0["security_id"], f0["weight"]))
        actual_end = dict(zip(f1["security_id"], f1["weight"]))
        fund_returns = returns_by_entity[fund]
        no_trade = drift_weights(start_weights, fund_returns)
        for sid in sorted(set(start_weights) | set(no_trade) | set(actual_end)):
            row0 = f0.loc[f0.security_id.eq(sid)]
            row1 = f1.loc[f1.security_id.eq(sid)]
            r0 = row0.iloc[0].to_dict() if len(row0) else {}
            r1 = row1.iloc[0].to_dict() if len(row1) else {}
            drift_rows.append({
                "fund": fund, "security_id": sid,
                "name": r0.get("name", r1.get("name", "")),
                "mapped_ticker": r0.get("mapped_ticker", ""),
                "start_weight_pct_equity": 100.0 * start_weights.get(sid, 0.0),
                "total_return_pct": 100.0 * fund_returns.get(sid, 0.0),
                "no_trade_end_weight_pct_equity": 100.0 * no_trade.get(sid, 0.0),
                "actual_end_weight_pct_equity": 100.0 * actual_end.get(sid, 0.0),
                "price_status": "priced" if sid not in unpriced_by_entity[fund] else "unpriced_zero_return_assumption",
            })
        for benchmark in benchmark_entities:
            b0, b1 = portfolios[(benchmark, args.start_date)], portfolios[(benchmark, args.end_date)]
            b_start = dict(zip(b0["security_id"], b0["weight"]))
            b_end = dict(zip(b1["security_id"], b1["weight"]))
            gate_pass = all(
                coverage_by_entity[entity]["mapping_coverage_gate_pass"]
                and coverage_by_entity[entity]["price_gate_pass"]
                for entity in (fund, benchmark)
            )
            if gate_pass:
                result = decompose_active_share(
                    start_weights, no_trade, actual_end, b_start, b_end,
                    f"{benchmark} ({roles[benchmark]} ETF proxy)",
                )
                result.update({"fund": fund, "benchmark_entity": benchmark, "calculation_status": "calculated",
                               "fund_price_coverage_pct": coverage_by_entity[fund]["price_coverage_pct_starting_equity"],
                               "benchmark_price_coverage_pct": coverage_by_entity[benchmark]["price_coverage_pct_starting_equity"]})
                decompositions.append(result)
                sens = missing_return_sensitivity(
                    start_weights, fund_returns, unpriced_by_entity[fund], actual_end,
                    [(benchmark, b_start, b_end)],
                )
                for row in sens:
                    row.update({"fund": fund, "benchmark_entity": benchmark})
                    sensitivity_rows.append(row)
            else:
                decompositions.append({
                    "fund": fund, "benchmark_entity": benchmark,
                    "benchmark": f"{benchmark} ({roles[benchmark]} ETF proxy)",
                    "calculation_status": "withheld_price_coverage_below_95pct",
                    "fund_price_coverage_pct": coverage_by_entity[fund]["price_coverage_pct_starting_equity"],
                    "benchmark_price_coverage_pct": coverage_by_entity[benchmark]["price_coverage_pct_starting_equity"],
                })

    for row in decompositions:
        if row["calculation_status"] == "calculated":
            if abs(float(row["component_reconciliation_error_pp"])) > 1e-8:
                raise AssertionError(f"Active Share decomposition failed to reconcile: {row}")

    metrics = {
        "study": "C.2 six-fund no-trade drift cohort",
        "start_date": args.start_date, "end_date": args.end_date,
        "funds": fund_entities, "benchmark_proxies": benchmark_entities,
        "price_source": "Yahoo Finance auto-adjusted close via yfinance",
        "return_currency": "USD",
        "quote_currency_policy": "No Yahoo suffix is treated as USD because the mapper selects U.S. composite/OTC USD listings; .T is JPY and converted with JPY=X quoted as JPY per USD; unknown suffixes are excluded from price coverage.",
        "fx_source": "Yahoo Finance JPY=X endpoint rates; USD return = (1 + local return) * (JPY_per_USD_start / JPY_per_USD_end) - 1.",
        "yfinance_version": yfinance_version, "pandas_version": pd.__version__,
        "price_download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "price_coverage_gate_pct": 100.0 * MIN_PRICE_COVERAGE,
        "price_coverage_by_entity": coverage_rows,
        "portfolio_metadata": portfolio_meta,
        "decomposition_count_calculated": sum(x["calculation_status"] == "calculated" for x in decompositions),
        "decomposition_count_withheld": sum(x["calculation_status"] != "calculated" for x in decompositions),
        "active_share_decomposition": decompositions,
        "unpriced_return_sensitivity": sensitivity_rows,
        "interpretation": (
            "Common-equity sleeves are normalized to 100%. No-trade fund weights grow starting holdings "
            "by auto-adjusted Yahoo prices from the exact start date to exact end date, converted "
            "to USD when a supported non-USD listing is priced. Quote currency and FX conversion are audited; "
            "unsupported currencies or missing FX endpoints are not counted as priced. Price coverage "
            "must clear 95% separately for each fund and benchmark ETF proxy. ETF holdings are proxies, "
            "not official index constituent files. The portfolio-change residual is descriptive, not "
            "causal or synonymous with manager trading; flows, corporate actions, cash/derivatives, and "
            "reporting differences may contribute."
        ),
    }
    write_csv(out / "c2_cohort_price_coverage_by_entity.csv", coverage_rows)
    write_csv(out / "c2_cohort_security_total_returns.csv", price_audit)
    write_csv(out / "c2_cohort_fx_conversion_audit.csv",
              [row for row in price_audit if row.get("quote_currency", "USD") != "USD"])
    write_csv(out / "c2_cohort_entity_security_prices.csv", price_rows)
    write_csv(out / "c2_cohort_fund_security_drift.csv", drift_rows)
    write_csv(out / "c2_cohort_active_share_decomposition.csv", decompositions)
    write_csv(out / "c2_cohort_unpriced_return_sensitivity.csv", sensitivity_rows)
    (out / "c2_cohort_no_trade_drift_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    lines = [
        "# C.2 Six-Fund No-Trade Drift and Active Share",
        "",
        f"Period: {args.start_date} to {args.end_date}. Price source: Yahoo Finance auto-adjusted close (yfinance {yfinance_version}).",
        "",
        "| Entity | Role | Ticker mapping coverage (%) | Price coverage (%) | Mapping gate | Price gate | Unpriced weight (%) |",
        "|---|---|---:|---|---:|",
    ]
    for row in coverage_rows:
        lines.append(f"| {row['entity']} | {row['role']} | {row['ticker_mapping_coverage_pct_starting_equity']:.3f} | {row['price_coverage_pct_starting_equity']:.3f} | {'PASS' if row['mapping_coverage_gate_pass'] else 'FAIL'} | {'PASS' if row['price_gate_pass'] else 'FAIL'} | {row['unpriced_starting_equity_weight_pct']:.3f} |")
    lines += [
        "",
        "## Active Share decomposition",
        "",
        "| Fund | Benchmark ETF proxy | Status | AS start (%) | AS actual end (%) | Fund price drift (pp) | Benchmark weight change (pp) | Portfolio change beyond drift (pp) | Reconciliation error (pp) |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in decompositions:
        if row["calculation_status"] == "calculated":
            lines.append(f"| {row['fund']} | {row['benchmark_entity']} | calculated | {row['active_share_actual_start_pct']:.3f} | {row['active_share_actual_end_pct']:.3f} | {row['fund_price_drift_component_pp']:.3f} | {row['benchmark_weight_change_component_pp']:.3f} | {row['actual_portfolio_change_beyond_drift_pp']:.3f} | {row['component_reconciliation_error_pp']:.10f} |")
        else:
            lines.append(f"| {row['fund']} | {row['benchmark_entity']} | WITHHELD: price coverage below 95% | — | — | — | — | — | — |")
    lines += [
        "",
        "## Interpretation limits",
        "",
        "All portfolios are normalized to their reported common-equity sleeves. SPY and IWB are ETF holding proxies, not official S&P 500 or Russell 1000 constituent files. The portfolio-change residual is not a causal estimate of manager trading; it may reflect flows, corporate actions, cash or derivatives, and reporting differences. Unpriced start holdings remain in the baseline at zero return and are tested at -100%, 0%, and +100% where the fund/benchmark pair clears the price gate.",
    ]
    (out / "C2_COHORT_NO_TRADE_DRIFT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "coverage": coverage_rows,
        "calculated_decompositions": metrics["decomposition_count_calculated"],
        "withheld_decompositions": metrics["decomposition_count_withheld"],
    }, indent=2))


if __name__ == "__main__":
    main()
