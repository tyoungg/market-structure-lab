#!/usr/bin/env python3
"""Map C.2 cohort starting-equity identifiers to listed tickers using OpenFIGI v3."""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd
import requests

OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"
START_DATE = "2025-06-30"
INVALID = {"", "N/A", "NA", "NONE", "XXXX", "000000000"}


def valid(value: str) -> bool:
    return str(value or "").strip().upper() not in INVALID


def security_id(row: dict) -> str:
    isin = str(row.get("isin", "")).strip().upper()
    cusip = str(row.get("cusip", "")).strip().upper()
    ticker = str(row.get("ticker", "")).strip().upper()
    name = str(row.get("name", "")).strip().upper()
    if valid(isin):
        return "ISIN:" + isin
    if valid(cusip):
        return "CUSIP:" + cusip
    if valid(ticker):
        return "TICKER:" + ticker
    return "NAME:" + " ".join(name.split())


def build_security_universe(holdings: pd.DataFrame) -> tuple[list[dict], pd.DataFrame]:
    start = holdings[
        holdings["report_date"].eq(START_DATE)
        & holdings["role"].eq("fund")
        & holdings["is_common_equity"].astype(str).str.lower().eq("true")
    ].copy()
    if start.empty:
        raise ValueError("No starting-date fund common-equity holdings found")
    start["weight_pct_nav_num"] = pd.to_numeric(start["pct_net_assets"], errors="coerce").fillna(0.0)
    start["security_id"] = start.apply(lambda r: security_id(r.to_dict()), axis=1)
    rows = []
    for sid, group in start.groupby("security_id", sort=True):
        isins = sorted({str(x).strip().upper() for x in group["isin"] if valid(x)})
        cusips = sorted({str(x).strip().upper() for x in group["cusip"] if valid(x)})
        tickers = sorted({str(x).strip().upper() for x in group["ticker"] if valid(x)})
        primary_type, primary_value = ("ID_ISIN", isins[0]) if isins else (("ID_CUSIP", cusips[0]) if cusips else ("", ""))
        fallback_type, fallback_value = ("ID_CUSIP", cusips[0]) if isins and cusips else (("ID_ISIN", isins[0]) if cusips and isins else ("", ""))
        rows.append({
            "security_id": sid,
            "name": next((str(x) for x in group["name"] if str(x).strip()), ""),
            "cusip": cusips[0] if cusips else "",
            "isin": isins[0] if isins else "",
            "cusip_count": len(cusips),
            "isin_count": len(isins),
            "nport_tickers": "|".join(tickers),
            "ticker_count": len(tickers),
            "investment_country": next((str(x).strip().upper() for x in group["investment_country"] if valid(x)), ""),
            "funds": "|".join(sorted(set(group["entity"].astype(str)))),
            "fund_count": int(group["entity"].nunique()),
            "starting_weight_pct_nav_sum": float(group["weight_pct_nav_num"].sum()),
            "primary_identifier_type": primary_type,
            "primary_identifier_value": primary_value,
            "fallback_identifier_type": fallback_type,
            "fallback_identifier_value": fallback_value,
        })
    universe = pd.DataFrame(rows)
    return rows, start


def select_ticker(matches: list[dict], country: str = "") -> dict:
    equity = [
        x for x in matches
        if x.get("ticker") and x.get("marketSector") in {"Equity", None}
        and x.get("securityType2", "Common Stock") not in {"Option", "Warrant"}
    ]
    if not equity:
        return {"status": "no_ticker_match", "selected": None, "candidate_tickers": []}
    us = [x for x in equity if str(x.get("exchCode", "")).upper() == "US"]
    country_matches = [x for x in equity if country and str(x.get("exchCode", "")).upper() == country.upper()]
    preferred = us or country_matches or equity
    tickers = sorted({str(x.get("ticker", "")).strip().upper() for x in preferred if x.get("ticker")})
    if len(tickers) == 1:
        selected = next(x for x in preferred if str(x.get("ticker", "")).strip().upper() == tickers[0])
        return {"status": "unique_ticker", "selected": selected, "candidate_tickers": tickers}
    return {"status": "ambiguous_ticker", "selected": None, "candidate_tickers": tickers}


def map_batch(jobs: list[dict], api_key: str = "") -> list[dict]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-OPENFIGI-APIKEY"] = api_key
    for attempt in range(5):
        response = requests.post(OPENFIGI_URL, headers=headers, json=jobs, timeout=60)
        if response.status_code == 429:
            wait = float(response.headers.get("retry-after", "60"))
            time.sleep(max(wait, 1.0))
            continue
        if response.status_code in {500, 502, 503, 504}:
            time.sleep(2 ** attempt)
            continue
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list) or len(payload) != len(jobs):
            raise ValueError(f"Unexpected OpenFIGI response length: expected {len(jobs)}")
        return payload
    raise RuntimeError("OpenFIGI request retries exhausted")


def run_mapping(universe: list[dict], api_key: str = "") -> tuple[list[dict], list[dict]]:
    raw_log = []
    output = []
    pending_primary = []
    direct_ticker_ids = set()

    for row in universe:
        tickers = [x for x in row["nport_tickers"].split("|") if x]
        if len(tickers) == 1:
            output.append({
                **row, "mapping_status": "nport_ticker", "mapped_ticker": tickers[0],
                "mapped_exch_code": row["investment_country"], "mapped_figi": "",
                "mapping_source": "N-PORT reported ticker", "candidate_tickers": tickers,
                "primary_response_json": "", "fallback_response_json": "",
            })
            direct_ticker_ids.add(row["security_id"])
        elif len(tickers) > 1:
            output.append({
                **row, "mapping_status": "conflicting_nport_tickers", "mapped_ticker": "",
                "mapped_exch_code": "", "mapped_figi": "", "mapping_source": "N-PORT ticker conflict",
                "candidate_tickers": tickers, "primary_response_json": "", "fallback_response_json": "",
            })
            direct_ticker_ids.add(row["security_id"])
        elif row["primary_identifier_type"]:
            pending_primary.append(row)
        else:
            output.append({
                **row, "mapping_status": "missing_identifiers", "mapped_ticker": "",
                "mapped_exch_code": "", "mapped_figi": "", "mapping_source": "",
                "candidate_tickers": [], "primary_response_json": "", "fallback_response_json": "",
            })

    primary_results = {}
    for offset in range(0, len(pending_primary), 10):
        batch_rows = pending_primary[offset:offset + 10]
        jobs = [{
            "idType": row["primary_identifier_type"],
            "idValue": row["primary_identifier_value"],
            "marketSecDes": "Equity",
            "includeUnlistedEquities": True,
        } for row in batch_rows]
        responses = map_batch(jobs, api_key)
        for row, job, response in zip(batch_rows, jobs, responses):
            primary_results[row["security_id"]] = response
            raw_log.append({"security_id": row["security_id"], "stage": "primary",
                            "job": job, "response": response})
        if offset + 10 < len(pending_primary):
            time.sleep(2.5 if not api_key else 0.3)

    fallback_rows = []
    primary_selected = {}
    for row in pending_primary:
        response = primary_results.get(row["security_id"], {})
        selected = select_ticker(response.get("data", []), row["investment_country"]) if isinstance(response, dict) else {
            "status": "mapping_error", "selected": None, "candidate_tickers": []
        }
        primary_selected[row["security_id"]] = selected
        if selected["status"] != "unique_ticker" and row["fallback_identifier_type"]:
            fallback_rows.append(row)

    fallback_results = {}
    for offset in range(0, len(fallback_rows), 10):
        batch_rows = fallback_rows[offset:offset + 10]
        jobs = [{
            "idType": row["fallback_identifier_type"],
            "idValue": row["fallback_identifier_value"],
            "marketSecDes": "Equity",
            "includeUnlistedEquities": True,
        } for row in batch_rows]
        responses = map_batch(jobs, api_key)
        for row, job, response in zip(batch_rows, jobs, responses):
            fallback_results[row["security_id"]] = response
            raw_log.append({"security_id": row["security_id"], "stage": "fallback",
                            "job": job, "response": response})
        if offset + 10 < len(fallback_rows):
            time.sleep(2.5 if not api_key else 0.3)

    for row in pending_primary:
        sid = row["security_id"]
        primary_response = primary_results.get(sid, {})
        primary = primary_selected.get(sid, {"status": "mapping_error", "selected": None, "candidate_tickers": []})
        fallback_response = fallback_results.get(sid, {})
        fallback = select_ticker(fallback_response.get("data", []), row["investment_country"]) if fallback_response else {
            "status": "not_attempted", "selected": None, "candidate_tickers": []
        }
        chosen = None
        source = ""
        status = primary["status"]
        if primary["status"] == "unique_ticker":
            chosen = primary["selected"]
            source = "OpenFIGI primary identifier"
            status = "openfigi_primary_unique_ticker"
        elif fallback["status"] == "unique_ticker":
            chosen = fallback["selected"]
            source = "OpenFIGI fallback identifier"
            status = "openfigi_fallback_unique_ticker"
        elif primary["status"] == "ambiguous_ticker" or fallback["status"] == "ambiguous_ticker":
            status = "ambiguous_ticker"
        elif primary.get("status") == "no_ticker_match" and fallback.get("status") in {"no_ticker_match", "not_attempted"}:
            status = "no_ticker_match"
        elif primary.get("status") == "mapping_error" or fallback.get("status") == "mapping_error":
            status = "mapping_error"

        output.append({
            **row,
            "mapping_status": status,
            "mapped_ticker": str(chosen.get("ticker", "")).upper() if chosen else "",
            "mapped_exch_code": str(chosen.get("exchCode", "")).upper() if chosen else "",
            "mapped_figi": chosen.get("figi", "") if chosen else "",
            "mapping_source": source,
            "candidate_tickers": sorted(set(primary.get("candidate_tickers", []) + fallback.get("candidate_tickers", []))),
            "primary_response_json": json.dumps(primary_response, sort_keys=True),
            "fallback_response_json": json.dumps(fallback_response, sort_keys=True),
        })

    output_by_id = {row["security_id"]: row for row in output}
    start = pd.read_csv(Path(args_input_placeholder), dtype=str).fillna("") if False else None
    return [output_by_id[row["security_id"]] for row in universe], raw_log


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="c2_nport_cohort")
    parser.add_argument("--out", default="c2_nport_cohort")
    args = parser.parse_args()
    source = Path(args.input)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    holdings = pd.read_csv(source / "nport_cohort_common_equity.csv", dtype=str).fillna("")
    universe, start = build_security_universe(holdings)
    api_key = os.environ.get("OPENFIGI_API_KEY", "").strip()
    mapped, raw_log = run_mapping(universe, api_key)

    mapping_df = pd.DataFrame(mapped)
    map_by_id = {row["security_id"]: row for row in mapped}
    coverage_rows = []
    for entity, group in start.groupby("entity", sort=True):
        total = pd.to_numeric(group["pct_net_assets"], errors="coerce").fillna(0.0).sum()
        mapped_weight = 0.0
        unresolved_weight = 0.0
        for row in group.to_dict("records"):
            m = map_by_id.get(row["security_id"], {})
            w = float(pd.to_numeric(row["pct_net_assets"], errors="coerce") or 0.0)
            if m.get("mapped_ticker"):
                mapped_weight += w
            else:
                unresolved_weight += w
        coverage = 100.0 * mapped_weight / total if total else 0.0
        coverage_rows.append({
            "fund": entity,
            "starting_equity_weight_pct_nav": total,
            "mapped_equity_weight_pct_nav": mapped_weight,
            "unmapped_equity_weight_pct_nav": unresolved_weight,
            "ticker_mapping_coverage_pct_starting_equity": coverage,
            "unmapped_weight_pct_starting_equity": 100.0 - coverage,
            "common_equity_position_rows": len(group),
            "unique_securities": int(group.apply(lambda r: security_id(r.to_dict()), axis=1).nunique()),
        })

    summary = {
        "mapping_source": "OpenFIGI v3 Mapping API plus N-PORT-reported tickers",
        "api_key_used": bool(api_key),
        "unauthenticated_rate_limit": "25 requests/minute; 10 jobs/request",
        "include_unlisted_equities": True,
        "unique_starting_securities": len(universe),
        "direct_nport_ticker_rows": sum(x["mapping_status"] == "nport_ticker" for x in mapped),
        "openfigi_primary_unique": sum(x["mapping_status"] == "openfigi_primary_unique_ticker" for x in mapped),
        "openfigi_fallback_unique": sum(x["mapping_status"] == "openfigi_fallback_unique_ticker" for x in mapped),
        "ambiguous": sum(x["mapping_status"] in {"ambiguous_ticker", "conflicting_nport_tickers"} for x in mapped),
        "no_match": sum(x["mapping_status"] in {"no_ticker_match", "missing_identifiers"} for x in mapped),
        "mapping_error": sum(x["mapping_status"] == "mapping_error" for x in mapped),
        "fund_coverage": coverage_rows,
        "interpretation": "Ticker mapping audit only. Historical adjusted-price retrieval and no-trade drift calculation are separate steps.",
    }

    mapping_df.to_csv(out / "c2_security_identifier_map.csv", index=False)
    pd.DataFrame(coverage_rows).to_csv(out / "c2_identifier_mapping_coverage_by_fund.csv", index=False)
    (out / "c2_openfigi_raw_results.json").write_text(json.dumps(raw_log, indent=2), encoding="utf-8")
    (out / "c2_identifier_mapping_metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# C.2 Security Identifier Mapping Audit",
        "",
        f"Mapped {summary['unique_starting_securities']} unique starting-date securities using N-PORT tickers and OpenFIGI v3.",
        "",
        "| Fund | Ticker mapping coverage (% starting equity) | Unmapped weight (%) |",
        "|---|---:|---:|",
    ]
    for row in coverage_rows:
        lines.append(f"| {row['fund']} | {row['ticker_mapping_coverage_pct_starting_equity']:.3f} | {row['unmapped_weight_pct_starting_equity']:.3f} |")
    lines += [
        "",
        f"- Direct N-PORT ticker mappings: {summary['direct_nport_ticker_rows']}",
        f"- Unique OpenFIGI primary mappings: {summary['openfigi_primary_unique']}",
        f"- Unique OpenFIGI fallback mappings: {summary['openfigi_fallback_unique']}",
        f"- Ambiguous/conflicting mappings: {summary['ambiguous']}",
        f"- No-match/missing-identifier mappings: {summary['no_match']}",
        f"- Mapping errors: {summary['mapping_error']}",
        "",
        "All OpenFIGI candidate responses are retained in the artifact. Ambiguous mappings are not auto-resolved. This report measures ticker mapping coverage, not price coverage.",
    ]
    (out / "C2_IDENTIFIER_MAPPING_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
