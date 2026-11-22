#!/usr/bin/env python3
"""Acquire and validate a small, frozen SEC N-PORT holdings sample for C.2."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests


FILINGS = [
    {
        "entity": "Optimum Large Cap Growth Fund", "role": "fund", "report_date": "2025-06-30",
        "cik": "0001227523", "series_id": "S000002422", "series_name": "Optimum Large Cap Growth Fund",
        "accession": "0001752724-25-207530",
        "url": "https://www.sec.gov/Archives/edgar/data/1227523/000175272425207530/primary_doc.xml",
    },
    {
        "entity": "Optimum Large Cap Growth Fund", "role": "fund", "report_date": "2025-09-30",
        "cik": "0001227523", "series_id": "S000002422", "series_name": "Optimum Large Cap Growth Fund",
        "accession": "0000940400-25-009486",
        "url": "https://www.sec.gov/Archives/edgar/data/1227523/000094040025009486/primary_doc.xml",
    },
    {
        "entity": "SPY", "role": "benchmark_sp500", "report_date": "2025-06-30",
        "cik": "0000884394", "series_id": "", "series_name": "SPDR S&P 500 ETF Trust",
        "accession": "0001752724-25-211156",
        "url": "https://www.sec.gov/Archives/edgar/data/884394/000175272425211156/primary_doc.xml",
    },
    {
        "entity": "SPY", "role": "benchmark_sp500", "report_date": "2025-09-30",
        "cik": "0000884394", "series_id": "", "series_name": "SPDR S&P 500 ETF Trust",
        "accession": "0001410368-25-031962",
        "url": "https://www.sec.gov/Archives/edgar/data/884394/000141036825031962/primary_doc.xml",
    },
    {
        "entity": "IWB", "role": "benchmark_russell1000", "report_date": "2025-06-30",
        "cik": "0001100663", "series_id": "S000004347", "series_name": "iShares Russell 1000 ETF",
        "accession": "0001752724-25-204367",
        "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272425204367/primary_doc.xml",
    },
    {
        "entity": "IWB", "role": "benchmark_russell1000", "report_date": "2025-09-30",
        "cik": "0001100663", "series_id": "S000004347", "series_name": "iShares Russell 1000 ETF",
        "accession": "0001004726-25-002043",
        "url": "https://www.sec.gov/Archives/edgar/data/1100663/000100472625002043/primary_doc.xml",
    },
]


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def descendants(node: ET.Element, name: str) -> list[ET.Element]:
    return [el for el in node.iter() if local_name(el.tag) == name]


def first_text(node: ET.Element, name: str, default: str = "") -> str:
    found = descendants(node, name)
    if not found:
        return default
    return (found[0].text or "").strip()


def number(value: str) -> float | None:
    if value is None or str(value).strip() in ("", "N/A", "XXXX"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def position_identifiers(position: ET.Element) -> tuple[str, str, str, str]:
    cusip = first_text(position, "cusip")
    isin = ""
    ticker = ""
    others = []
    for el in position.iter():
        tag = local_name(el.tag)
        value = (el.attrib.get("value") or (el.text or "")).strip()
        if tag == "isin" and value:
            isin = value
        elif tag == "ticker" and value:
            ticker = value.upper()
        elif tag == "other" and value:
            desc = (el.attrib.get("otherDesc") or "").strip()
            others.append({"description": desc, "value": value})
            if desc.lower() in {"ticker", "ticker symbol", "trading symbol"} and not ticker:
                ticker = value.upper()
    return cusip, isin, ticker, json.dumps(others, sort_keys=True)


def parse_nport_xml(xml_bytes: bytes, spec: dict) -> tuple[dict, list[dict]]:
    root = ET.fromstring(xml_bytes)
    gen = descendants(root, "genInfo")
    gen_info = gen[0] if gen else root
    fund_nodes = descendants(root, "fundInfo")
    fund_info = fund_nodes[0] if fund_nodes else root

    meta = {
        **{k: spec[k] for k in ("entity", "role", "report_date", "cik", "series_id", "series_name", "accession", "url")},
        "xml_reg_cik": first_text(gen_info, "regCik") or first_text(root, "regCik"),
        "xml_reg_name": first_text(gen_info, "regName") or first_text(root, "regName"),
        "xml_series_id": first_text(gen_info, "seriesId"),
        "xml_series_name": first_text(gen_info, "seriesName"),
        "rep_pd_date": first_text(gen_info, "repPdDate"),
        "net_assets_usd": number(first_text(fund_info, "netAssets")),
        "total_assets_usd": number(first_text(fund_info, "totAssets")),
        "total_liabilities_usd": number(first_text(fund_info, "totLiabs")),
        "position_count": 0,
    }

    positions = []
    for index, pos in enumerate(descendants(root, "invstOrSec"), start=1):
        cusip, isin, ticker, other_ids = position_identifiers(pos)
        asset_cat = first_text(pos, "assetCat")
        if not asset_cat:
            conditional = descendants(pos, "assetConditional")
            if conditional:
                asset_cat = conditional[0].attrib.get("assetCat", "")
        payoff = first_text(pos, "payoffProfile")
        val = number(first_text(pos, "valUSD"))
        pct = number(first_text(pos, "pctVal"))
        record = {
            "entity": spec["entity"], "role": spec["role"], "report_date": meta["rep_pd_date"],
            "accession": spec["accession"], "series_id": meta["xml_series_id"],
            "position_number": index,
            "name": first_text(pos, "name"), "title": first_text(pos, "title"),
            "cusip": cusip, "isin": isin, "ticker": ticker, "other_identifiers_json": other_ids,
            "balance": number(first_text(pos, "balance")), "units": first_text(pos, "units"),
            "currency": first_text(pos, "curCd"), "value_usd": val, "pct_net_assets": pct,
            "asset_category": asset_cat, "payoff_profile": payoff,
            "is_common_equity": asset_cat == "EC" and payoff.lower() == "long",
        }
        positions.append(record)

    meta["position_count"] = len(positions)
    return meta, positions


def validate_identity(meta: dict, spec: dict) -> None:
    if meta["rep_pd_date"] != spec["report_date"]:
        raise ValueError(f"{spec['entity']} {spec['accession']}: repPdDate {meta['rep_pd_date']!r} != {spec['report_date']}")
    if meta["xml_reg_cik"] and meta["xml_reg_cik"].zfill(10) != spec["cik"].zfill(10):
        raise ValueError(f"{spec['entity']} {spec['accession']}: registrant CIK mismatch {meta['xml_reg_cik']}")
    if spec["series_id"] and meta["xml_series_id"] != spec["series_id"]:
        raise ValueError(f"{spec['entity']} {spec['accession']}: series ID {meta['xml_series_id']!r} != {spec['series_id']}")
    observed_name = meta["xml_series_name"] or meta["xml_reg_name"]
    if spec["series_name"].lower() not in observed_name.lower():
        raise ValueError(f"{spec['entity']} {spec['accession']}: series/registrant name mismatch: {observed_name!r}")


def summarize(meta: dict, positions: list[dict], byte_count: int, digest: str) -> dict:
    equity = [p for p in positions if p["is_common_equity"]]
    pct = lambda rows: sum((p["pct_net_assets"] or 0.0) for p in rows)
    equity_weight = pct(equity)
    ticker_weight = pct([p for p in equity if p["ticker"]])
    cusip_weight = pct([p for p in equity if p["cusip"]])
    isin_weight = pct([p for p in equity if p["isin"]])
    cusips = [p["cusip"] for p in equity if p["cusip"]]
    summary = {
        **meta,
        "xml_bytes": byte_count,
        "xml_sha256": digest,
        "equity_position_count": len(equity),
        "equity_weight_pct_net_assets": round(equity_weight, 6),
        "equity_ticker_coverage_pct_of_equity": round(100 * ticker_weight / equity_weight, 4) if equity_weight else 0,
        "equity_cusip_coverage_pct_of_equity": round(100 * cusip_weight / equity_weight, 4) if equity_weight else 0,
        "equity_isin_coverage_pct_of_equity": round(100 * isin_weight / equity_weight, 4) if equity_weight else 0,
        "unique_equity_cusips": len(set(cusips)),
        "duplicate_equity_cusip_rows": len(cusips) - len(set(cusips)),
        "all_position_pct_net_assets": round(pct(positions), 6),
    }
    return summary


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row.keys()))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def download_xml(spec: dict, out_path: Path, email: str) -> bytes:
    headers = {
        "User-Agent": f"Market Structure Lab research contact {email}",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov",
    }
    last_error = None
    for attempt in range(4):
        try:
            response = requests.get(spec["url"], headers=headers, timeout=90)
            if response.status_code == 200 and response.content:
                out_path.write_bytes(response.content)
                return response.content
            last_error = f"HTTP {response.status_code}: {response.text[:300]}"
            if response.status_code not in (403, 429, 500, 502, 503, 504):
                break
        except requests.RequestException as exc:
            last_error = repr(exc)
        time.sleep(2 ** attempt)
    raise RuntimeError(f"SEC download failed for {spec['accession']}: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="c2_nport_pilot")
    args = parser.parse_args()
    email = os.environ.get("SEC_CONTACT_EMAIL", "").strip()
    if not email or "@" not in email:
        raise RuntimeError("SEC_CONTACT_EMAIL must be set to a valid contact email in the workflow environment")

    out = Path(args.out)
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    all_positions, equity_positions, summaries = [], [], []

    for i, spec in enumerate(FILINGS):
        raw_path = raw_dir / f"{spec['role']}_{spec['report_date']}_{spec['accession'].replace('-', '')}.xml"
        xml_bytes = download_xml(spec, raw_path, email)
        digest = hashlib.sha256(xml_bytes).hexdigest()
        meta, positions = parse_nport_xml(xml_bytes, spec)
        validate_identity(meta, spec)
        if not positions or meta["net_assets_usd"] is None:
            raise ValueError(f"Incomplete N-PORT report for {spec['entity']} {spec['report_date']}")
        summary = summarize(meta, positions, len(xml_bytes), digest)
        summaries.append(summary)
        all_positions.extend(positions)
        equity_positions.extend(p for p in positions if p["is_common_equity"])
        print(
            f"Validated {spec['entity']} {meta['rep_pd_date']}: "
            f"positions={len(positions)}, common_equity={summary['equity_position_count']}, "
            f"equity_weight={summary['equity_weight_pct_net_assets']:.2f}%"
        )
        time.sleep(0.5)

    if len(summaries) != 6:
        raise AssertionError(f"Expected six N-PORT reports, got {len(summaries)}")
    for entity in ("Optimum Large Cap Growth Fund", "SPY", "IWB"):
        dates = sorted(x["rep_pd_date"] for x in summaries if x["entity"] == entity)
        if dates != ["2025-06-30", "2025-09-30"]:
            raise AssertionError(f"{entity}: expected two consecutive report dates, got {dates}")

    write_csv(out / "nport_pilot_all_positions.csv", all_positions)
    write_csv(out / "nport_pilot_common_equity.csv", equity_positions)
    write_csv(out / "nport_pilot_manifest.csv", summaries)
    metrics = {
        "pilot": "Optimum Large Cap Growth Fund vs SPY and IWB",
        "report_dates": ["2025-06-30", "2025-09-30"],
        "reports_validated": len(summaries),
        "total_positions": len(all_positions),
        "common_equity_positions": len(equity_positions),
        "reports": summaries,
        "interpretation": "Acquisition and XML parsing only. No security returns or no-trade drift estimate has been calculated.",
    }
    (out / "nport_pilot_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    lines = [
        "# C.2 N-PORT Acquisition Pilot",
        "",
        "All six frozen SEC N-PORT-P XML reports passed report-date and entity/series identity checks.",
        "",
        "| Entity | Report date | Positions | Common equity | Equity weight (% NAV) | Ticker coverage (% equity) | CUSIP coverage (% equity) |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for x in summaries:
        lines.append(
            f"| {x['entity']} | {x['rep_pd_date']} | {x['position_count']} | {x['equity_position_count']} | "
            f"{x['equity_weight_pct_net_assets']:.2f} | {x['equity_ticker_coverage_pct_of_equity']:.2f} | "
            f"{x['equity_cusip_coverage_pct_of_equity']:.2f} |"
        )
    lines += [
        "",
        "This run validates holdings acquisition and parsing only. It does not calculate security returns, Active Share, or no-trade drift.",
        "Review CUSIP/ISIN and ticker coverage before proceeding to price mapping and return adjustment.",
    ]
    (out / "C2_NPORT_ACQUISITION_PILOT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"reports_validated": len(summaries), "total_positions": len(all_positions),
                      "common_equity_positions": len(equity_positions)}, indent=2))


if __name__ == "__main__":
    main()
