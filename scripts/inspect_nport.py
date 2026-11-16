#!/usr/bin/env python3
"""Inspect and extract selected tables from an SEC Form N-PORT quarterly ZIP.

The script preserves SEC source tables as tab-delimited text. It does not classify
funds, resolve amendments, map securities, or calculate portfolio weights.
Those are later, separately validated steps.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

SEC_BASE = "https://www.sec.gov/files/dera/data/form-n-port-data-sets"
DEFAULT_TABLES = [
    "SUBMISSION",
    "REGISTRANT",
    "FUND_REPORTED_INFO",
    "FUND_REPORTED_HOLDING",
    "IDENTIFIERS",
    "FUND_VAR_INFO",
]


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quarter", default="2026q3",
                   help="SEC archive quarter, e.g. 2026q3 (default: 2026q3)")
    p.add_argument("--archive", type=Path,
                   help="Use an already-downloaded SEC ZIP instead of downloading")
    p.add_argument("--download", action="store_true",
                   help="Download the SEC ZIP if --archive is not supplied")
    p.add_argument("--user-agent", default=os.getenv("SEC_USER_AGENT"),
                   help="SEC-compliant User-Agent; or set SEC_USER_AGENT environment variable")
    p.add_argument("--output-dir", type=Path, default=Path("data/nport"),
                   help="Output root (default: data/nport)")
    p.add_argument("--all-tables", action="store_true",
                   help="Extract every tabular file in the archive, not just core tables")
    p.add_argument("--count-rows", action="store_true",
                   help="Count rows in extracted TSVs (can take several minutes)")
    return p.parse_args()


def download_archive(url: str, destination: Path, user_agent: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"})
    print(f"Downloading {url}")
    print(f"Destination: {destination}")
    with urlopen(request, timeout=120) as response, destination.open("wb") as out:
        total = response.headers.get("Content-Length")
        if total:
            print(f"Expected size: {int(total) / (1024**2):,.1f} MiB")
        shutil.copyfileobj(response, out, length=1024 * 1024)
    print(f"Downloaded {destination.stat().st_size / (1024**2):,.1f} MiB")


def table_name(member: str) -> str | None:
    """Return uppercase stem for TSV/TXT/CSV members, otherwise None."""
    path = Path(member)
    if path.suffix.lower() not in {".tsv", ".txt", ".csv"}:
        return None
    return path.stem.upper()


def main():
    args = parse_args()
    quarter = args.quarter.lower().replace("-", "")
    if len(quarter) != 6 or quarter[:4].isdigit() is False or quarter[4:] not in {
        "q1", "q2", "q3", "q4"
    }:
        raise SystemExit("Quarter must look like 2026q3.")

    url = f"{SEC_BASE}/{quarter}_nport.zip"
    archive = args.archive or Path("data/nport_raw") / f"{quarter}_nport.zip"

    if args.archive is None:
        if not args.download:
            raise SystemExit(
                "No archive supplied. Re-run with --download (SEC archive is several hundred MB), "
                "or provide --archive /path/to/archive.zip."
            )
        if not args.user_agent:
            raise SystemExit(
                "Set SEC_USER_AGENT to an identifying contact string or pass --user-agent. "
                "Please use a real contact address you control."
            )
        if not archive.exists():
            download_archive(url, archive, args.user_agent)
        else:
            print(f"Using existing archive: {archive}")

    if not archive.exists():
        raise SystemExit(f"Archive not found: {archive}")

    output_dir = args.output_dir / quarter
    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive) as zf:
        members = zf.namelist()
        tabular = [(m, table_name(m)) for m in members]
        tabular = [(m, n) for m, n in tabular if n]
        selected_names = None if args.all_tables else set(DEFAULT_TABLES)
        selected = [(m, n) for m, n in tabular if selected_names is None or n in selected_names]

        if not selected:
            raise SystemExit(
                "No expected N-PORT tables found. Inspect archive contents; "
                "the SEC archive layout may have changed."
            )

        # Preserve the SEC-provided metadata file when present.
        metadata_members = [
            m for m in members
            if "metadata" in Path(m).name.lower() and Path(m).suffix.lower() in {".json", ".csv"}
        ]
        for member in metadata_members:
            target = output_dir / Path(member).name
            with zf.open(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)

        table_manifest = []
        for member, name in selected:
            target = output_dir / f"{name}.tsv"
            with zf.open(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)

            # Inspect column names from the extracted tab-delimited source.
            try:
                columns = pd.read_csv(target, sep="\t", dtype=str, nrows=0).columns.tolist()
            except Exception as exc:
                columns = []
                print(f"WARNING: Could not read header for {name}: {exc}")

            row_count = None
            if args.count_rows:
                row_count = 0
                with target.open("r", encoding="utf-8-sig", newline="") as f:
                    row_count = max(sum(1 for _ in csv.reader(f, delimiter="\t")) - 1, 0)

            table_manifest.append({
                "table": name,
                "source_member": member,
                "extracted_file": str(target),
                "columns": columns,
                "row_count": row_count,
                "file_size_bytes": target.stat().st_size,
            })
            print(f"{name}: {len(columns)} columns" +
                  (f", {row_count:,} rows" if row_count is not None else ""))

    manifest = {
        "source": "U.S. Securities and Exchange Commission Form N-PORT Data Sets",
        "source_url": url,
        "quarter": quarter,
        "archive": str(archive),
        "archive_size_bytes": archive.stat().st_size,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "script_version": "0.1.0",
        "notes": [
            "Extracted tables are preserved as SEC-provided tab-delimited text.",
            "No amendment resolution or fund classification has been performed.",
            "No holdings have been filtered or normalized.",
            "SEC datasets include only filings publicly disseminated by the Commission.",
        ],
        "tables": table_manifest,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nWrote manifest: {manifest_path}")
    print(f"Extracted {len(table_manifest)} tables to {output_dir}")
    print("Next: review the manifest and reconcile selected records to the original SEC filing.")


if __name__ == "__main__":
    main()
