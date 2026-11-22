#!/usr/bin/env python3
"""Calculate a public-data no-trade drift pilot from frozen N-PORT holdings."""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


START_DATE = "2025-06-30"
END_DATE = "2025-09-30"
PRICE_START = "2025-06-30"
PRICE_END_EXCLUSIVE = "2025-10-01"
MIN_PRICE_COVERAGE = 0.95


def security_identifier(row: dict) -> str:
    cusip = str(row.get("cusip", "")).strip().upper()
    isin = str(row.get("isin", "")).strip().upper()
    ticker = str(row.get("ticker", "")).strip().upper()
    name = str(row.get("name", "")).strip().upper()
    invalid = {"", "N/A", "NA", "NONE", "XXXX", "000000000"}
    if isin not in invalid:
        return "ISIN:" + isin
    if cusip not in invalid:
        return "CUSIP:" + cusip
    if ticker not in invalid:
        return "TICKER:" + ticker
    return "NAME:" + re.sub(r"\s+", " ", name)


def aggregate_portfolio(holdings: pd.DataFrame, entity: str, report_date: str) -> tuple[dict, pd.DataFrame]:
    subset = holdings[
        holdings["entity"].eq(entity)
        & holdings["report_date"].eq(report_date)
        & holdings["is_common_equity"].astype(str).str.lower().eq("true")
    ].copy()
    if subset.empty:
        raise ValueError(f"No common-equity holdings for {entity} {report_date}")
    subset["pct_net_assets_num"] = pd.to_numeric(subset["pct_net_assets"], errors="coerce").fillna(0.0)
    subset["security_id"] = subset.apply(lambda r: security_identifier(r.to_dict()), axis=1)
    rows = []
    for security_id, group in subset.groupby("security_id", sort=True):
        invalid = {"", "N/A", "NA", "NONE", "XXXX", "000000000"}
        tickers = sorted({str(x).strip().upper() for x in group["ticker"] if str(x).strip().upper() not in invalid})
        if len(tickers) > 1:
            raise ValueError(f"Conflicting tickers for {security_id}: {tickers}")
        rows.append({
            "entity": entity, "report_date": report_date, "security_id": security_id,
            "name": next((str(x) for x in group["name"] if str(x).strip()), ""),
            "title": next((str(x) for x in group["title"] if str(x).strip()), ""),
            "cusip": next((str(x) for x in group["cusip"] if str(x).strip().upper() not in invalid), ""),
            "isin": next((str(x) for x in group["isin"] if str(x).strip().upper() not in invalid), ""),
            "ticker": tickers[0] if tickers else "",
            "weight_pct_nav": float(group["pct_net_assets_num"].sum()),
            "source_position_rows": int(len(group)),
        })
    result = pd.DataFrame(rows)
    equity_weight_pct_nav = float(result["weight_pct_nav"].sum())
    if equity_weight_pct_nav <= 0:
        raise ValueError(f"Non-positive equity weight for {entity} {report_date}")
    result["weight"] = result["weight_pct_nav"] / equity_weight_pct_nav
    result["weight_pct_equity"] = result["weight"] * 100.0
    result = result.sort_values("security_id").reset_index(drop=True)
    return {"entity": entity, "report_date": report_date, "equity_weight_pct_nav": equity_weight_pct_nav,
            "position_rows": len(subset), "unique_securities": len(result)}, result


def active_share(weights_a: dict[str, float], weights_b: dict[str, float]) -> float:
    universe = set(weights_a) | set(weights_b)
    return 0.5 * sum(abs(weights_a.get(k, 0.0) - weights_b.get(k, 0.0)) for k in universe)


def drift_weights(start_weights: dict[str, float], returns: dict[str, float]) -> dict[str, float]:
    grown = {key: weight * (1.0 + returns.get(key, 0.0)) for key, weight in start_weights.items()}
    total = sum(grown.values())
    if total <= 0:
        raise ValueError("No-trade portfolio has non-positive value after returns")
    return {key: value / total for key, value in grown.items()}


def decompose_active_share(
    fund_start: dict[str, float], fund_no_trade_end: dict[str, float], fund_actual_end: dict[str, float],
    benchmark_start: dict[str, float], benchmark_end: dict[str, float], benchmark_name: str,
) -> dict:
    as_start = active_share(fund_start, benchmark_start)
    as_no_trade_vs_start = active_share(fund_no_trade_end, benchmark_start)
    as_no_trade_vs_end = active_share(fund_no_trade_end, benchmark_end)
    as_actual_end = active_share(fund_actual_end, benchmark_end)
    fund_price_drift = as_no_trade_vs_start - as_start
    benchmark_change = as_no_trade_vs_end - as_no_trade_vs_start
    portfolio_change = as_actual_end - as_no_trade_vs_end
    actual_change = as_actual_end - as_start
    gap_universe = set(fund_no_trade_end) | set(fund_actual_end)
    reallocation_gap = 0.5 * sum(abs(fund_actual_end.get(k, 0.0) - fund_no_trade_end.get(k, 0.0)) for k in gap_universe)
    return {
        "benchmark": benchmark_name,
        "active_share_actual_start_pct": 100 * as_start,
        "active_share_no_trade_end_vs_start_benchmark_pct": 100 * as_no_trade_vs_start,
        "active_share_no_trade_end_vs_end_benchmark_pct": 100 * as_no_trade_vs_end,
        "active_share_actual_end_pct": 100 * as_actual_end,
        "actual_active_share_change_pp": 100 * actual_change,
        "fund_price_drift_component_pp": 100 * fund_price_drift,
        "benchmark_weight_change_component_pp": 100 * benchmark_change,
        "actual_portfolio_change_beyond_drift_pp": 100 * portfolio_change,
        "component_reconciliation_error_pp": 100 * (actual_change - fund_price_drift - benchmark_change - portfolio_change),
        "actual_vs_no_trade_end_portfolio_gap_pct": 100 * reallocation_gap,
    }


def missing_return_sensitivity(
    start_weights: dict[str, float], base_returns: dict[str, float], unpriced_ids: list[str],
    fund_actual_end: dict[str, float], benchmark_pairs: list[tuple[str, dict[str, float], dict[str, float]]],
) -> list[dict]:
    rows = []
    for scenario, assumed_return in [("minus_100_pct", -1.0), ("zero_return", 0.0), ("plus_100_pct", 1.0)]:
        scenario_returns = dict(base_returns)
        for security_id in unpriced_ids:
            scenario_returns[security_id] = assumed_return
        drifted = drift_weights(start_weights, scenario_returns)
        for benchmark_name, benchmark_start, benchmark_end in benchmark_pairs:
            as_no_trade_end = active_share(drifted, benchmark_end)
            as_actual_end = active_share(fund_actual_end, benchmark_end)
            gap_universe = set(drifted) | set(fund_actual_end)
            gap = 0.5 * sum(abs(fund_actual_end.get(k, 0.0) - drifted.get(k, 0.0)) for k in gap_universe)
            rows.append({
                "unpriced_return_scenario": scenario,
                "assumed_total_return_pct": assumed_return * 100,
                "benchmark": benchmark_name,
                "active_share_no_trade_end_vs_end_benchmark_pct": 100 * as_no_trade_end,
                "active_share_actual_end_pct": 100 * as_actual_end,
                "actual_portfolio_change_beyond_drift_pp": 100 * (as_actual_end - as_no_trade_end),
                "actual_vs_no_trade_end_portfolio_gap_pct": 100 * gap,
            })
    return rows


def yahoo_symbol(ticker: str, isin: str = "") -> str:
    value = ticker.strip().upper()
    # The N-PORT ticker for Japanese listings is often numeric without an exchange suffix.
    if value.isdigit() and isin.strip().upper().startswith("JP"):
        return value + ".T"
    return value.replace(".", "-").replace("/", "-")


def _extract_close(data: pd.DataFrame, ticker: str, requested_count: int) -> pd.Series | None:
    if data is None or data.empty:
        return None
    if isinstance(data.columns, pd.MultiIndex):
        level0 = list(data.columns.get_level_values(0))
        level1 = list(data.columns.get_level_values(1))
        if ticker in level0:
            sub = data[ticker]
            return sub["Close"] if "Close" in sub.columns else None
        if ticker in level1:
            sub = data.xs(ticker, axis=1, level=1)
            return sub["Close"] if "Close" in sub.columns else None
        return None
    if requested_count == 1 and "Close" in data.columns:
        return data["Close"]
    return None


def download_total_returns(tickers: list[str], ticker_isins: dict[str, str] = None) -> tuple[dict, list[dict], str]:
    import yfinance as yf

    ticker_isins = ticker_isins or {}
    unique = sorted(set(tickers))
    symbol_map = {ticker: yahoo_symbol(ticker, ticker_isins.get(ticker, "")) for ticker in unique}
    yahoo_symbols = sorted(set(symbol_map.values()))
    prices, audit = {}, []
    batch_size = 15
    for start in range(0, len(yahoo_symbols), batch_size):
        batch = yahoo_symbols[start:start + batch_size]
        data = pd.DataFrame()
        last_error = ""
        for attempt in range(3):
            try:
                data = yf.download(
                    tickers=batch, start=PRICE_START, end=PRICE_END_EXCLUSIVE,
                    auto_adjust=True, actions=False, progress=False, threads=False,
                    group_by="ticker", timeout=30,
                )
                if not data.empty:
                    break
                last_error = "empty response"
            except Exception as exc:  # yfinance raises several transport/rate-limit exceptions
                last_error = repr(exc)
            time.sleep(2 ** attempt)
        for original, yahoo in symbol_map.items():
            if yahoo not in batch:
                continue
            close = _extract_close(data, yahoo, len(batch))
            if close is None:
                continue
            series = pd.to_numeric(close, errors="coerce").dropna()
            dates = pd.to_datetime(series.index).date
            by_date = {d.isoformat(): float(v) for d, v in zip(dates, series.values)}
            p0, p1 = by_date.get(START_DATE), by_date.get(END_DATE)
            if p0 and p1 and p0 > 0 and p1 > 0:
                ret = p1 / p0 - 1.0
                prices[original] = {"yahoo_symbol": yahoo, "start_adj_close": p0,
                                    "end_adj_close": p1, "total_return": ret, "status": "priced"}
                audit.append({"ticker": original, **prices[original]})
            else:
                audit.append({"ticker": original, "yahoo_symbol": yahoo, "start_adj_close": p0 or "",
                              "end_adj_close": p1 or "", "total_return": "", "status": "missing_exact_endpoint_price",
                              "batch_error": last_error})
        time.sleep(1.0)

    # Retry any missing endpoints individually; do not silently treat a listed security as unpriced.
    audit_by_ticker = {row["ticker"]: row for row in audit}
    for original in unique:
        if original in prices:
            continue
        yahoo = symbol_map[original]
        last_error = ""
        for attempt in range(3):
            try:
                data = yf.download(
                    tickers=yahoo, start=PRICE_START, end=PRICE_END_EXCLUSIVE,
                    auto_adjust=True, actions=False, progress=False, threads=False, timeout=30,
                )
                close = _extract_close(data, yahoo, 1)
                if close is not None:
                    series = pd.to_numeric(close, errors="coerce").dropna()
                    dates = pd.to_datetime(series.index).date
                    by_date = {d.isoformat(): float(v) for d, v in zip(dates, series.values)}
                    p0, p1 = by_date.get(START_DATE), by_date.get(END_DATE)
                    if p0 and p1 and p0 > 0 and p1 > 0:
                        info = {"yahoo_symbol": yahoo, "start_adj_close": p0, "end_adj_close": p1,
                                "total_return": p1 / p0 - 1.0, "status": "priced_individual_fallback"}
                        prices[original] = info
                        audit_by_ticker[original] = {"ticker": original, **info}
                        break
                    last_error = "missing exact endpoint in individual response"
                else:
                    last_error = "individual response missing Close column"
            except Exception as exc:
                last_error = repr(exc)
            time.sleep(2 ** attempt)
        if original not in prices:
            existing = audit_by_ticker.get(original, {"ticker": original, "yahoo_symbol": yahoo})
            existing["status"] = "missing_exact_endpoint_price"
            existing["fallback_error"] = last_error
            audit_by_ticker[original] = existing
    audit = [audit_by_ticker[ticker] for ticker in unique]
    return prices, audit, getattr(yf, "__version__", "unknown")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row.keys()))
    pd.DataFrame(rows, columns=fields).to_csv(path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="c2_nport_pilot")
    parser.add_argument("--out", default="c2_no_trade_drift")
    args = parser.parse_args()
    source = Path(args.input)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    holdings = pd.read_csv(source / "nport_pilot_common_equity.csv", dtype=str).fillna("")
    fund_meta0, fund0 = aggregate_portfolio(holdings, "Optimum Large Cap Growth Fund", START_DATE)
    fund_meta1, fund1 = aggregate_portfolio(holdings, "Optimum Large Cap Growth Fund", END_DATE)
    spy_meta0, spy0 = aggregate_portfolio(holdings, "SPY", START_DATE)
    spy_meta1, spy1 = aggregate_portfolio(holdings, "SPY", END_DATE)
    iwb_meta0, iwb0 = aggregate_portfolio(holdings, "IWB", START_DATE)
    iwb_meta1, iwb1 = aggregate_portfolio(holdings, "IWB", END_DATE)

    start_tickers = sorted({x for x in fund0["ticker"] if x})
    ticker_isins = dict(zip(fund0["ticker"], fund0["isin"]))
    prices, price_audit, yfinance_version = download_total_returns(start_tickers, ticker_isins)
    start_weights = dict(zip(fund0["security_id"], fund0["weight"]))
    returns_by_security = {}
    price_rows = []
    priced_weight = 0.0
    unpriced_weight = 0.0
    ticker_by_security = dict(zip(fund0["security_id"], fund0["ticker"]))
    for row in fund0.to_dict("records"):
        ticker = row["ticker"]
        security_id = row["security_id"]
        if ticker and ticker in prices:
            ret = prices[ticker]["total_return"]
            status = prices[ticker].get("status", "priced")
            priced_weight += row["weight"]
            price_info = prices[ticker]
        else:
            ret = 0.0
            status = "unpriced_zero_return_assumption"
            unpriced_weight += row["weight"]
            price_info = {}
        returns_by_security[security_id] = ret
        price_rows.append({
            "security_id": security_id, "ticker": ticker, "name": row["name"],
            "start_weight_pct_equity": row["weight"] * 100,
            "total_return_pct": ret * 100, "price_status": status,
            "start_adj_close": price_info.get("start_adj_close", ""),
            "end_adj_close": price_info.get("end_adj_close", ""),
            "yahoo_symbol": price_info.get("yahoo_symbol", ""),
        })
    price_coverage = priced_weight / sum(start_weights.values())
    drifted_weights = drift_weights(start_weights, returns_by_security)

    fund_end_weights = dict(zip(fund1["security_id"], fund1["weight"]))
    spy_start_weights = dict(zip(spy0["security_id"], spy0["weight"]))
    spy_end_weights = dict(zip(spy1["security_id"], spy1["weight"]))
    iwb_start_weights = dict(zip(iwb0["security_id"], iwb0["weight"]))
    iwb_end_weights = dict(zip(iwb1["security_id"], iwb1["weight"]))

    decompositions = [
        decompose_active_share(start_weights, drifted_weights, fund_end_weights,
                               spy_start_weights, spy_end_weights, "SPY (S&P 500 ETF proxy)"),
        decompose_active_share(start_weights, drifted_weights, fund_end_weights,
                               iwb_start_weights, iwb_end_weights, "IWB (Russell 1000 ETF proxy)"),
    ]
    unpriced_ids = [row["security_id"] for row in price_rows if row["price_status"] == "unpriced_zero_return_assumption"]
    unpriced_sensitivity = missing_return_sensitivity(
        start_weights, returns_by_security, unpriced_ids, fund_end_weights,
        [("SPY (S&P 500 ETF proxy)", spy_start_weights, spy_end_weights),
         ("IWB (Russell 1000 ETF proxy)", iwb_start_weights, iwb_end_weights)],
    )

    security_rows = []
    for security_id in sorted(set(start_weights) | set(drifted_weights) | set(fund_end_weights)):
        row0 = fund0.loc[fund0.security_id.eq(security_id)]
        row1 = fund1.loc[fund1.security_id.eq(security_id)]
        r0 = row0.iloc[0].to_dict() if len(row0) else {}
        security_rows.append({
            "security_id": security_id,
            "name": r0.get("name", row1.iloc[0]["name"] if len(row1) else ""),
            "cusip": r0.get("cusip", row1.iloc[0]["cusip"] if len(row1) else ""),
            "isin": r0.get("isin", row1.iloc[0]["isin"] if len(row1) else ""),
            "ticker": ticker_by_security.get(security_id, r0.get("ticker", "")),
            "start_weight_pct_equity": 100 * start_weights.get(security_id, 0.0),
            "total_return_pct": 100 * returns_by_security.get(security_id, 0.0),
            "no_trade_end_weight_pct_equity": 100 * drifted_weights.get(security_id, 0.0),
            "actual_end_weight_pct_equity": 100 * fund_end_weights.get(security_id, 0.0),
            "price_status": next((x["price_status"] for x in price_rows if x["security_id"] == security_id), "not_held_at_start"),
        })

    status = "calculated" if price_coverage >= MIN_PRICE_COVERAGE else "withheld_price_coverage_below_95pct"
    metrics = {
        "pilot": "Optimum Large Cap Growth Fund vs SPY and IWB",
        "security_matching_priority": "ISIN, then CUSIP, then ticker, then normalized name",
        "start_date": START_DATE, "end_date": END_DATE,
        "price_source": "Yahoo Finance adjusted close via yfinance",
        "yfinance_version": yfinance_version,
        "pandas_version": pd.__version__,
        "price_download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "price_coverage_pct_starting_equity_value": round(100 * price_coverage, 6),
        "unpriced_starting_equity_weight_pct": round(100 * unpriced_weight, 8),
        "priced_starting_equity_weight_pct": round(100 * priced_weight, 8),
        "price_coverage_gate": MIN_PRICE_COVERAGE,
        "drift_estimate_status": status,
        "portfolio_metadata": [fund_meta0, fund_meta1, spy_meta0, spy_meta1, iwb_meta0, iwb_meta1],
        "active_share_decomposition": decompositions if status == "calculated" else [],
        "unpriced_return_sensitivity": unpriced_sensitivity if status == "calculated" else [],
        "interpretation": "Single-fund, three-month public-data pilot. Active Share uses common-equity weights normalized to the equity sleeve. Decomposition is descriptive, not causal. ETF holdings are benchmark proxies, not official index files.",
    }

    write_csv(out / "security_total_returns.csv", price_audit)
    write_csv(out / "fund_security_drift.csv", security_rows)
    write_csv(out / "active_share_decomposition.csv", decompositions if status == "calculated" else [])
    write_csv(out / "unpriced_return_sensitivity.csv", unpriced_sensitivity if status == "calculated" else [])
    (out / "c2_no_trade_drift_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    lines = [
        "# C.2 No-Trade Drift Pilot",
        "",
        f"**Status:** {status}",
        "",
        f"- Fund: Optimum Large Cap Growth Fund (series S000002422)",
        f"- Period: {START_DATE} to {END_DATE}",
        f"- Price coverage: {100 * price_coverage:.6f}% of starting common-equity value",
        f"- Unpriced starting weight carried at zero return: {100 * unpriced_weight:.8f}% of equity",
        f"- Price source: Yahoo Finance adjusted close (yfinance {yfinance_version})",
        "",
        "## Active Share decomposition",
        "",
        "| Benchmark proxy | AS actual start | AS no-trade end vs start benchmark | AS no-trade end vs end benchmark | AS actual end | Fund price drift (pp) | Benchmark change (pp) | Portfolio change beyond drift (pp) | Reconciliation error (pp) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    if status == "calculated":
        for x in decompositions:
            lines.append(
                f"| {x['benchmark']} | {x['active_share_actual_start_pct']:.3f}% | "
                f"{x['active_share_no_trade_end_vs_start_benchmark_pct']:.3f}% | "
                f"{x['active_share_no_trade_end_vs_end_benchmark_pct']:.3f}% | "
                f"{x['active_share_actual_end_pct']:.3f}% | {x['fund_price_drift_component_pp']:.3f} | "
                f"{x['benchmark_weight_change_component_pp']:.3f} | "
                f"{x['actual_portfolio_change_beyond_drift_pp']:.3f} | "
                f"{x['component_reconciliation_error_pp']:.8f} |"
            )
    else:
        lines.append("| Withheld | — | — | — | — | — | — | — | — |")
    lines += [
        "",
        "## Unpriced-position return sensitivity",
        "",
        "| Assumed return on all unpriced starting positions | Benchmark proxy | No-trade AS at end vs. end benchmark | Actual AS at end | Portfolio-change component (pp) | Actual-vs-no-trade gap (%) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    if status == "calculated":
        for x in unpriced_sensitivity:
            lines.append(
                f"| {x['assumed_total_return_pct']:.0f}% | {x['benchmark']} | "
                f"{x['active_share_no_trade_end_vs_end_benchmark_pct']:.3f}% | "
                f"{x['active_share_actual_end_pct']:.3f}% | "
                f"{x['actual_portfolio_change_beyond_drift_pp']:.3f} | "
                f"{x['actual_vs_no_trade_end_portfolio_gap_pct']:.3f} |"
            )
    else:
        lines.append("| Not calculated | — | — | — | — | — |")
    lines += [
        "",
        "The unpriced positions are retained in the starting portfolio with a zero-return assumption in the baseline and reported explicitly. The sensitivity table applies -100%, 0%, and +100% total returns to those positions.",
        "Do not interpret the portfolio-change component as pure manager trading: it can include flows, corporate actions, derivative/cash changes, and data/reporting differences.",
    ]
    (out / "C2_NO_TRADE_DRIFT_PILOT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "price_coverage_pct": 100 * price_coverage,
                      "active_share_decomposition": decompositions}, indent=2))


if __name__ == "__main__":
    main()
