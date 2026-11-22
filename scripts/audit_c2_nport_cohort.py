#!/usr/bin/env python3
"""Acquire a predeclared multi-fund SEC N-PORT cohort for C.2."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
from pathlib import Path

from audit_c2_nport_pilot import download_xml, parse_nport_xml, summarize, validate_identity, write_csv


EXPECTED_DATES = ["2025-06-30", "2025-09-30", "2025-12-31"]


def read_manifest(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"entity", "role", "style_bucket", "report_date", "cik", "series_id",
                "series_name", "accession", "url"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"Manifest must contain columns: {sorted(required)}")
    return rows


def validate_manifest(specs: list[dict]) -> None:
    if len(specs) != 24:
        raise ValueError(f"Expected 24 filing rows, found {len(specs)}")
    funds = sorted({x["entity"] for x in specs if x["role"] == "fund"})
    benchmarks = sorted({x["entity"] for x in specs if x["role"].startswith("benchmark_")})
    if len(funds) != 6 or benchmarks != ["IWB", "SPY"]:
        raise ValueError(f"Unexpected cohort composition: funds={funds}, benchmarks={benchmarks}")
    for entity in funds + benchmarks:
        dates = sorted(x["report_date"] for x in specs if x["entity"] == entity)
        if dates != EXPECTED_DATES:
            raise ValueError(f"{entity}: expected report dates {EXPECTED_DATES}, got {dates}")
    if len({(x["entity"], x["report_date"]) for x in specs}) != 16:
        raise ValueError("Duplicate entity/report-date rows in manifest")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="research/C2_COHORT_MANIFEST.csv")
    parser.add_argument("--out", default="c2_nport_cohort")
    args = parser.parse_args()

    email = os.environ.get("SEC_CONTACT_EMAIL", "").strip()
    if not email or "@" not in email:
        raise RuntimeError("SEC_CONTACT_EMAIL must be set to a valid contact email")

    specs = read_manifest(Path(args.manifest))
    validate_manifest(specs)
    out = Path(args.out)
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    all_positions, common_equity, summaries = [], [], []
    for index, spec in enumerate(specs, start=1):
        slug = re.sub(r"[^A-Za-z0-9]+", "_", spec["entity"]).strip("_").lower()
        accession_slug = spec["accession"].replace("-", "")
        raw_path = raw_dir / f"{slug}_{spec['report_date']}_{accession_slug}.xml"
        xml_bytes = download_xml(spec, raw_path, email)
        digest = hashlib.sha256(xml_bytes).hexdigest()
        meta, positions = parse_nport_xml(xml_bytes, spec)
        meta["style_bucket"] = spec["style_bucket"]
        validate_identity(meta, spec)
        if not positions or meta["net_assets_usd"] is None:
            raise ValueError(f"Incomplete N-PORT report: {spec['entity']} {spec['report_date']}")
        for position in positions:
            position["style_bucket"] = spec["style_bucket"]
            position["series_name"] = meta["xml_series_name"] or meta["xml_reg_name"]
            position["cik"] = spec["cik"]
        summary = summarize(meta, positions, len(xml_bytes), digest)
        summaries.append(summary)
        all_positions.extend(positions)
        common_equity.extend(p for p in positions if p["is_common_equity"])
        print(
            f"[{index:02d}/{len(specs)}] {spec['entity']} {meta['rep_pd_date']} "
            f"positions={len(positions)} equity={summary['equity_position_count']} "
            f"equity_NAV={summary['equity_weight_pct_net_assets']:.2f}%"
        )
        time.sleep(0.5)

    funds = sorted({x["entity"] for x in specs if x["role"] == "fund"})
    benchmarks = sorted({x["entity"] for x in specs if x["role"].startswith("benchmark_")})
    metrics = {
        "cohort": "six active-management candidates across growth, value, and blend buckets",
        "holdings_dates": EXPECTED_DATES,
        "fund_count": len(funds),
        "benchmark_count": len(benchmarks),
        "report_count": len(summaries),
        "total_positions": len(all_positions),
        "common_equity_positions": len(common_equity),
        "funds": funds,
        "benchmarks": benchmarks,
        "reports": summaries,
        "interpretation": "Acquisition and identity validation only. Strategy adjudication and multi-fund no-trade drift calculation are separate next steps.",
    }

    write_csv(out / "nport_cohort_all_positions.csv", all_positions)
    write_csv(out / "nport_cohort_common_equity.csv", common_equity)
    write_csv(out / "nport_cohort_manifest.csv", summaries)
    (out / "nport_cohort_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    lines = [
        "# C.2 Multi-Fund N-PORT Acquisition Audit",
        "",
        f"Validated {len(summaries)} of {len(specs)} frozen SEC N-PORT-P filings for {len(funds)} candidate funds and {len(benchmarks)} ETF benchmark proxies.",
        "",
        "| Entity | Style bucket | Report date | Positions | Common equity | Equity weight (% NAV) | Ticker coverage (% equity) | CUSIP coverage (% equity) | ISIN coverage (% equity) |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for x in summaries:
        lines.append(
            f"| {x['entity']} | {x['style_bucket'] or 'Benchmark'} | {x['rep_pd_date']} | "
            f"{x['position_count']} | {x['equity_position_count']} | {x['equity_weight_pct_net_assets']:.2f} | "
            f"{x['equity_ticker_coverage_pct_of_equity']:.2f} | "
            f"{x['equity_cusip_coverage_pct_of_equity']:.2f} | "
            f"{x['equity_isin_coverage_pct_of_equity']:.2f} |"
        )
    lines += [
        "",
        "This is an acquisition/identity audit only. It does not classify the funds as active, calculate Active Share, or calculate no-trade drift.",
        "Review prospectus strategy evidence and per-fund identifier/price coverage before proceeding.",
    ]
    (out / "C2_NPORT_COHORT_ACQUISITION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"fund_count": len(funds), "report_count": len(summaries),
                      "total_positions": len(all_positions), "common_equity_positions": len(common_equity)}, indent=2))


if __name__ == "__main__":
    main()
