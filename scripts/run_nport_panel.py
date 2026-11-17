#!/usr/bin/env python3
"""Build a multi-fund, multi-quarter N-PORT no-trade panel from public Parquet mirror.

Source tables are a public-domain SEC N-PORT data set mirrored as Parquet on
Hugging Face. The mirror is unofficial; SEC filings remain authoritative.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
import run_nport_pilot as pilot  # noqa: E402

DATASET_REPO = "trader298/sec-nport"
SOURCE_PARTITIONS = [(2025, 4), (2026, 1), (2026, 2), (2026, 3)]
REPORT_DATES = ["2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30"]
BENCHMARK_SERIES = "S000004310"

META_COLUMNS = {
    "SUBMISSION": ["ACCESSION_NUMBER", "FILING_DATE", "SUB_TYPE", "REPORT_DATE", "IS_LAST_FILING"],
    "FUND_REPORTED_INFO": ["ACCESSION_NUMBER", "SERIES_ID", "SERIES_NAME", "NET_ASSETS"],
    "REGISTRANT": ["ACCESSION_NUMBER", "CIK", "REGISTRANT_NAME"],
}
HOLDING_COLUMNS = [
    "ACCESSION_NUMBER", "HOLDING_ID", "ISSUER_NAME", "ISSUER_TITLE", "ISSUER_CUSIP",
    "BALANCE", "UNIT", "CURRENCY_CODE", "CURRENCY_VALUE", "EXCHANGE_RATE", "PERCENTAGE",
    "PAYOFF_PROFILE", "ASSET_CAT", "ISSUER_TYPE", "INVESTMENT_COUNTRY",
]
IDENTIFIER_COLUMNS = [
    "HOLDING_ID", "IDENTIFIERS_ID", "IDENTIFIER_ISIN", "IDENTIFIER_TICKER",
    "OTHER_IDENTIFIER", "OTHER_IDENTIFIER_DESC",
]


def partition_filename(table: str, year: int, quarter: int) -> str:
    return f"{table}/year={year}/quarter={quarter}/data.parquet"


def get_partition(table: str, year: int, quarter: int, cache_dir: Path) -> Path:
    path = hf_hub_download(
        repo_id=DATASET_REPO,
        repo_type="dataset",
        filename=partition_filename(table, year, quarter),
        cache_dir=str(cache_dir),
    )
    return Path(path)


def load_metadata(cache_dir: Path, partitions: list[tuple[int, int]], series_ids: set[str], dates: set[str] | None = None) -> pd.DataFrame:
    filing_parts: list[pd.DataFrame] = []
    for year, quarter in partitions:
        frames = {}
        for table, cols in META_COLUMNS.items():
            path = get_partition(table, year, quarter, cache_dir)
            frames[table] = pd.read_parquet(path, columns=cols)
        x = frames["SUBMISSION"].merge(
            frames["FUND_REPORTED_INFO"], on="ACCESSION_NUMBER", how="inner", validate="one_to_one"
        ).merge(
            frames["REGISTRANT"], on="ACCESSION_NUMBER", how="left", validate="one_to_one"
        )
        x["SOURCE_YEAR"] = year
        x["SOURCE_QUARTER"] = quarter
        x["REPORT_DATE"] = pd.to_datetime(x["REPORT_DATE"], errors="coerce").dt.strftime("%Y-%m-%d")
        x["FILING_DATE"] = pd.to_datetime(x["FILING_DATE"], errors="coerce")
        mask = x["SUB_TYPE"].isin(["NPORT-P", "NPORT-P/A"]) & x["SERIES_ID"].isin(series_ids)
        if dates is not None:
            mask &= x["REPORT_DATE"].isin(dates)
        x = x[mask].copy()
        filing_parts.append(x)
    if not filing_parts:
        return pd.DataFrame()
    all_filings = pd.concat(filing_parts, ignore_index=True)
    all_filings["SUBTYPE_RANK"] = all_filings["SUB_TYPE"].map({"NPORT-P": 1, "NPORT-P/A": 2})
    all_filings = all_filings.sort_values(
        ["SERIES_ID", "REPORT_DATE", "FILING_DATE", "SUBTYPE_RANK", "ACCESSION_NUMBER"]
    )
    all_filings["FILING_COUNT"] = all_filings.groupby(["SERIES_ID", "REPORT_DATE"])["ACCESSION_NUMBER"].transform("count")
    return all_filings.drop_duplicates(["SERIES_ID", "REPORT_DATE"], keep="last").reset_index(drop=True)


def _read_selected_holdings(path: Path, accessions: set[str]) -> pd.DataFrame:
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(path)
    pieces = []
    for batch in pf.iter_batches(columns=HOLDING_COLUMNS, batch_size=250_000):
        chunk = batch.to_pandas()
        chunk["ACCESSION_NUMBER"] = chunk["ACCESSION_NUMBER"].astype(str)
        chunk = chunk[chunk["ACCESSION_NUMBER"].isin(accessions)]
        if not chunk.empty:
            pieces.append(chunk)
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=HOLDING_COLUMNS)


def _read_selected_identifiers(path: Path, holding_ids: set[str]) -> pd.DataFrame:
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(path)
    pieces = []
    for batch in pf.iter_batches(columns=IDENTIFIER_COLUMNS, batch_size=300_000):
        chunk = batch.to_pandas()
        chunk["HOLDING_ID"] = chunk["HOLDING_ID"].astype(str)
        chunk = chunk[chunk["HOLDING_ID"].isin(holding_ids)]
        if not chunk.empty:
            pieces.append(chunk)
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=IDENTIFIER_COLUMNS)


def build_identifier_bridge(ids: pd.DataFrame) -> pd.DataFrame:
    if ids.empty:
        return pd.DataFrame(columns=["HOLDING_ID", "ISIN", "ISIN_COUNT", "TICKER", "TICKER_COUNT", "IDENTIFIER_ROWS"])
    rows = []
    for holding_id, group in ids.groupby("HOLDING_ID", sort=False):
        isins = sorted({str(v).strip() for v in group["IDENTIFIER_ISIN"].fillna("") if str(v).strip()})
        tickers = sorted({str(v).strip() for v in group["IDENTIFIER_TICKER"].fillna("") if str(v).strip()})
        rows.append({
            "HOLDING_ID": str(holding_id),
            "ISIN": isins[0] if len(isins) == 1 else "",
            "ISIN_COUNT": len(isins),
            "TICKER": tickers[0] if len(tickers) == 1 else "",
            "TICKER_COUNT": len(tickers),
            "IDENTIFIER_ROWS": len(group),
        })
    return pd.DataFrame(rows)


def attach_identifiers(holdings: pd.DataFrame, ids: pd.DataFrame) -> pd.DataFrame:
    h = holdings.copy()
    h["HOLDING_ID"] = h["HOLDING_ID"].astype(str)
    bridge = build_identifier_bridge(ids)
    h = h.merge(bridge, on="HOLDING_ID", how="left", validate="one_to_one")
    for col in ["ISIN", "TICKER"]:
        h[col] = h[col].fillna("")
    h["PCT_NAV"] = pd.to_numeric(h["PERCENTAGE"], errors="coerce") / 100.0
    cusip = h["ISSUER_CUSIP"].fillna("").astype(str).str.strip()
    h["SECURITY_KEY"] = h["ISIN"].where(h["ISIN"].ne(""), cusip.where(cusip.ne("") & cusip.ne("000000000"), "UNRESOLVED|" + h["HOLDING_ID"]))
    h["IDENTITY_STATUS"] = "ISIN"
    h.loc[h["ISIN"].eq("") & cusip.ne("") & cusip.ne("000000000"), "IDENTITY_STATUS"] = "CUSIP_FALLBACK"
    h.loc[h["SECURITY_KEY"].str.startswith("UNRESOLVED|"), "IDENTITY_STATUS"] = "UNRESOLVED"
    h.loc[pd.to_numeric(h["ISIN_COUNT"], errors="coerce").fillna(0).gt(1), "IDENTITY_STATUS"] = "AMBIGUOUS_ISIN"
    return h


def extract_all_selected_holdings(cache_dir: Path, selected: pd.DataFrame) -> pd.DataFrame:
    selected_parts = selected.groupby(["SOURCE_YEAR", "SOURCE_QUARTER"])
    output = []
    for (year, quarter), filings in selected_parts:
        accessions = set(filings["ACCESSION_NUMBER"].astype(str))
        holdings_path = get_partition("FUND_REPORTED_HOLDING", int(year), int(quarter), cache_dir)
        ids_path = get_partition("IDENTIFIERS", int(year), int(quarter), cache_dir)
        holdings = _read_selected_holdings(holdings_path, accessions)
        if holdings.empty:
            raise ValueError(f"No selected holdings found in source partition {year} Q{quarter}")
        holding_ids = set(holdings["HOLDING_ID"].astype(str))
        ids = _read_selected_identifiers(ids_path, holding_ids)
        output.append(attach_identifiers(holdings, ids))
    if not output:
        return pd.DataFrame()
    return pd.concat(output, ignore_index=True)


def equity_weights(holdings: pd.DataFrame, accession: str) -> tuple[pd.DataFrame, float]:
    x = holdings[(holdings["ACCESSION_NUMBER"].astype(str) == str(accession)) & (holdings["ASSET_CAT"] == "EC")].copy()
    x = x[x["PCT_NAV"].notna()]
    grouped = x.groupby("SECURITY_KEY", as_index=False).agg(
        PCT_NAV=("PCT_NAV", "sum"),
        ISSUER_NAME=("ISSUER_NAME", "first"),
        ISSUER_CUSIP=("ISSUER_CUSIP", "first"),
        ISIN=("ISIN", "first"),
        TICKER=("TICKER", "first"),
        IDENTITY_STATUS=("IDENTITY_STATUS", "first"),
        HOLDING_ROWS=("HOLDING_ID", "count"),
    )
    total = float(grouped["PCT_NAV"].sum())
    if total <= 0:
        raise ValueError(f"No positive common-equity sleeve for accession {accession}")
    grouped["EQUITY_WEIGHT"] = grouped["PCT_NAV"] / total
    return grouped, total


def aggregate_starting_security_candidates(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Combine metadata for shared keys without silently choosing conflicting tickers."""
    combined = pd.concat(frames, ignore_index=True)
    rows = []
    for security_key, group in combined.groupby("SECURITY_KEY", sort=False):
        record = {"SECURITY_KEY": security_key}
        for column in ["ISIN", "ISSUER_CUSIP", "TICKER", "ISSUER_NAME", "IDENTITY_STATUS"]:
            values = sorted({
                str(value).strip() for value in group.get(column, pd.Series(dtype=str)).fillna("")
                if str(value).strip()
            })
            record[column] = values[0] if len(values) == 1 else ""
            if column in {"TICKER", "ISSUER_NAME"}:
                record[f"{column}_CANDIDATES"] = json.dumps(values)
                record[f"{column}_CONFLICT"] = len(values) > 1
        record["SOURCE_FUND_COUNT"] = int(group.get("SECURITY_KEY", pd.Series(dtype=str)).nunique())
        rows.append(record)
    return pd.DataFrame(rows)


def build_interval_schedule(
    portfolios: dict[tuple[str, str], pd.DataFrame],
    fund_ids: set[str],
    benchmark_series: str,
    max_gap_days: int = 150,
) -> list[dict]:
    """Pair consecutive observed fund report dates; require benchmark at end date."""
    rows = []
    for series_id in sorted(fund_ids):
        observed = sorted(date for (sid, date) in portfolios if sid == series_id)
        for start_date, end_date in zip(observed[:-1], observed[1:]):
            gap_days = (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days
            if gap_days > max_gap_days:
                status = "REPORT_DATE_GAP_OVER_150_DAYS"
            elif (benchmark_series, end_date) not in portfolios:
                status = "BENCHMARK_OBSERVATION_MISSING_ON_FUND_END_DATE"
            else:
                status = "READY"
            rows.append({
                "SERIES_ID": series_id,
                "START_DATE": start_date,
                "END_DATE": end_date,
                "INTERVAL_DAYS": gap_days,
                "STATUS": status,
            })
    return rows


def strict_no_trade(start: pd.DataFrame, returns: pd.DataFrame) -> tuple[pd.DataFrame | None, float, list[str]]:
    x = start[["SECURITY_KEY", "EQUITY_WEIGHT"]].merge(
        returns[["SECURITY_KEY", "RETURN"]], on="SECURITY_KEY", how="left", validate="one_to_one"
    )
    missing = x.loc[x["RETURN"].isna(), "SECURITY_KEY"].astype(str).tolist()
    coverage = float(x.loc[x["RETURN"].notna(), "EQUITY_WEIGHT"].sum())
    if missing:
        return None, coverage, missing
    x["NT_RAW"] = x["EQUITY_WEIGHT"] * (1.0 + x["RETURN"])
    if (x["NT_RAW"] < 0).any() or x["NT_RAW"].sum() <= 0:
        return None, coverage, ["INVALID_NEGATIVE_OR_ZERO_GROSS_EQUITY_VALUE"]
    x["EQUITY_WEIGHT"] = x["NT_RAW"] / x["NT_RAW"].sum()
    return x[["SECURITY_KEY", "EQUITY_WEIGHT"]], coverage, []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--funds", type=Path, default=ROOT / "data/nport_panel/sample_funds.csv")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".cache/nport_hf")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/nport_panel_output")
    parser.add_argument("--start-date", default="2025-10-01")
    parser.add_argument("--end-date", default="2026-09-30")
    parser.add_argument("--dates", nargs="+", default=None,
                        help="Optional explicit report dates; normally use each fund's actual filing calendar.")
    parser.add_argument("--partitions", nargs="+", default=["2025Q4", "2026Q1", "2026Q2", "2026Q3"])
    parser.add_argument("--benchmark-series", default=BENCHMARK_SERIES)
    args = parser.parse_args()
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    partitions = [(int(token[:4]), int(token[-1])) for token in args.partitions]
    funds = pd.read_csv(args.funds, dtype=str).fillna("")
    fund_ids = set(funds["SERIES_ID"])
    all_series = fund_ids | {args.benchmark_series}
    explicit_dates = set(args.dates) if args.dates else None

    print(f"Loading actual filing dates from {DATASET_REPO}: {partitions}", flush=True)
    filings = load_metadata(args.cache_dir, partitions, all_series, explicit_dates)
    if filings.empty:
        raise ValueError("No filings found for selected fund series and source partitions")
    filings = filings[filings["REPORT_DATE"].between(args.start_date, args.end_date, inclusive="both")].copy()
    if filings.empty:
        raise ValueError("No filings found inside requested report-date window")

    # One latest valid filing per series/report date. NT notices are excluded.
    selected = filings.copy()
    selected.to_csv(args.output_dir / "filing_resolution.csv", index=False)

    fund_names = funds.set_index("SERIES_ID")["FUND_NAME"].to_dict()
    availability = selected.copy()
    availability["FUND_NAME"] = availability["SERIES_ID"].map(fund_names).fillna("IVV benchmark proxy")
    availability["OBSERVATION_ROLE"] = availability["SERIES_ID"].map(
        lambda x: "BENCHMARK" if x == args.benchmark_series else "FUND"
    )
    availability.sort_values(["SERIES_ID", "REPORT_DATE"]).to_csv(
        args.output_dir / "observation_availability.csv", index=False
    )

    selected_rows = selected[selected["ACCESSION_NUMBER"].notna()].copy()
    holdings = extract_all_selected_holdings(args.cache_dir, selected_rows)
    holdings.to_parquet(args.output_dir / "selected_holdings_with_identifiers.parquet", index=False)

    portfolios: dict[tuple[str, str], pd.DataFrame] = {}
    portfolio_meta: dict[tuple[str, str], dict] = {}
    for row in selected_rows.to_dict("records"):
        key = (str(row["SERIES_ID"]), str(row["REPORT_DATE"]))
        weights, equity_nav_share = equity_weights(holdings, str(row["ACCESSION_NUMBER"]))
        portfolios[key] = weights
        portfolio_meta[key] = {**row, "EQUITY_PCT_NAV": equity_nav_share * 100.0}
        weights.assign(SERIES_ID=key[0], REPORT_DATE=key[1]).to_csv(
            args.output_dir / f"weights_{key[0]}_{key[1]}.csv", index=False
        )
    if not portfolios:
        raise ValueError("No selected portfolio holdings were extracted")
    pd.concat([
        frame.assign(SERIES_ID=key[0], REPORT_DATE=key[1]) for key, frame in portfolios.items()
    ], ignore_index=True).to_parquet(args.output_dir / "portfolio_equity_weights.parquet", index=False)

    # Preserve the original SEC ZIP reconciliation gate for the June 2026 AB/IVV observation.
    ab_official = ROOT / "data/nport_pilot_inputs/ab_june_2026_equity.csv"
    ivv_compact = ROOT / "data/nport_pilot_inputs/ivv_june_2026_compact_equity.csv"
    if ab_official.exists() and ivv_compact.exists() and ("S000010411", "2026-06-30") in portfolios:
        ab_ref = pd.read_csv(ab_official, dtype={"SECURITY_KEY": str})
        ivv_ref = pd.read_csv(ivv_compact, dtype={"SECURITY_KEY": str})
        as_ref = pilot.active_share(ab_ref, ivv_ref)
        as_hf = pilot.active_share(portfolios[("S000010411", "2026-06-30")], portfolios[(args.benchmark_series, "2026-06-30")])
        pd.DataFrame([{"official_SEC_ZIP_reference_AS": as_ref, "HF_parquet_AS": as_hf, "absolute_difference": abs(as_ref-as_hf)}]).to_csv(
            args.output_dir / "official_sec_zip_crosscheck.csv", index=False
        )
        if abs(as_ref - as_hf) > 1e-6:
            raise ValueError(f"Hugging Face mirror does not reconcile to SEC ZIP pilot: {as_ref} vs {as_hf}")

    # Each fund contributes intervals between its own consecutive observed report dates.
    # A benchmark holding observation is required on the fund's ending report date.
    intervals_by_dates: dict[tuple[str, str], list[str]] = {}
    result_rows = []
    schedule = build_interval_schedule(portfolios, fund_ids, args.benchmark_series)
    for item in schedule:
        series_id = item["SERIES_ID"]
        base = {
            "SERIES_ID": series_id, "FUND_NAME": fund_names.get(series_id, series_id),
            "STYLE": funds.loc[funds.SERIES_ID == series_id, "STYLE"].iloc[0],
            "START_DATE": item["START_DATE"], "END_DATE": item["END_DATE"],
            "INTERVAL_DAYS": item["INTERVAL_DAYS"],
        }
        if item["STATUS"] == "READY":
            intervals_by_dates.setdefault((item["START_DATE"], item["END_DATE"]), []).append(series_id)
        else:
            result_rows.append({**base, "STATUS": item["STATUS"]})

    ticker_cache: dict[str, str] = {}
    ticker_source_cache: dict[str, str] = {}
    coverage_rows = []
    crosswalk_parts = []
    for (start_date, end_date), series_list in sorted(intervals_by_dates.items()):
        union = aggregate_starting_security_candidates(
            [portfolios[(sid, start_date)] for sid in series_list]
        )
        print(f"Fetching returns for {len(union)} unique starting securities: {start_date} to {end_date}", flush=True)
        returns = pilot.fetch_returns(
            union, start_date, end_date,
            ticker_cache=ticker_cache, ticker_source_cache=ticker_source_cache,
        )
        ticker_cache.update({
            str(r.SECURITY_KEY): str(r.TICKER_RESOLVED or "") for r in returns.itertuples()
        })
        ticker_source_cache.update({
            str(r.SECURITY_KEY): str(r.MAPPING_SOURCE or "") for r in returns.itertuples()
        })
        returns.to_csv(args.output_dir / f"security_returns_{start_date}_{end_date}.csv", index=False)
        cw = returns.copy()
        cw["INTERVAL_START"] = start_date
        cw["INTERVAL_END"] = end_date
        cw["RETURN_AVAILABLE"] = cw["RETURN"].notna()
        crosswalk_parts.append(cw)

        benchmark = portfolios[(args.benchmark_series, end_date)]
        for series_id in series_list:
            start = portfolios[(series_id, start_date)]
            actual = portfolios[(series_id, end_date)]
            meta0, meta1 = portfolio_meta[(series_id, start_date)], portfolio_meta[(series_id, end_date)]
            nt, coverage, missing_keys = strict_no_trade(start, returns)
            actual_as = pilot.active_share(actual, benchmark)
            no_trade_as = pilot.active_share(nt, benchmark) if nt is not None else None
            record = {
                "SERIES_ID": series_id, "FUND_NAME": fund_names.get(series_id, series_id),
                "STYLE": funds.loc[funds.SERIES_ID == series_id, "STYLE"].iloc[0],
                "START_DATE": start_date, "END_DATE": end_date,
                "INTERVAL_DAYS": (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days,
                "START_ACCESSION": meta0["ACCESSION_NUMBER"], "END_ACCESSION": meta1["ACCESSION_NUMBER"],
                "BENCHMARK_ACCESSION": portfolio_meta[(args.benchmark_series, end_date)]["ACCESSION_NUMBER"],
                "START_NET_ASSETS_USD": float(meta0["NET_ASSETS"]), "END_NET_ASSETS_USD": float(meta1["NET_ASSETS"]),
                "START_EQUITY_PCT_NAV": float(meta0["EQUITY_PCT_NAV"]), "END_EQUITY_PCT_NAV": float(meta1["EQUITY_PCT_NAV"]),
                "START_EQUITY_POSITIONS": int(len(start)), "END_EQUITY_POSITIONS": int(len(actual)),
                "RETURN_COVERAGE_START_EQUITY_WEIGHT": coverage, "POSITIONS_MISSING_RETURN": int(len(missing_keys)),
                "STRICT_NO_TRADE_CALCULATED": nt is not None,
                "ACTUAL_END_ACTIVE_SHARE_VS_IVV": actual_as,
                "NO_TRADE_ACTIVE_SHARE_VS_IVV": no_trade_as,
                "ACTUAL_MINUS_NO_TRADE_ACTIVE_SHARE": actual_as - no_trade_as if no_trade_as is not None else None,
                "STATUS": "CALCULATED" if nt is not None else "WITHHELD_INCOMPLETE_RETURN_COVERAGE",
            }
            result_rows.append(record)
            if missing_keys:
                missing = start[start.SECURITY_KEY.isin(missing_keys)]
                lookup = returns.set_index("SECURITY_KEY")
                for rec in missing.to_dict("records"):
                    details = lookup.loc[rec["SECURITY_KEY"]].to_dict()
                    coverage_rows.append({
                        "SERIES_ID": series_id, "FUND_NAME": fund_names.get(series_id, series_id),
                        "START_DATE": start_date, "END_DATE": end_date, **rec,
                        "TICKER_RESOLVED": details.get("TICKER_RESOLVED", ""),
                        "MAPPING_SOURCE": details.get("MAPPING_SOURCE", ""),
                        "NPORT_TICKER": details.get("NPORT_TICKER", ""),
                        "RETURN_MISSING_REASON": "NO_PRICE_RETURN_OR_UNRESOLVED_TICKER",
                    })
            if nt is not None:
                nt.assign(SERIES_ID=series_id, START_DATE=start_date, END_DATE=end_date).to_csv(
                    args.output_dir / f"no_trade_weights_{series_id}_{start_date}_{end_date}.csv", index=False
                )

    results = pd.DataFrame(result_rows)
    results.to_csv(args.output_dir / "fund_interval_results.csv", index=False)
    pd.DataFrame(coverage_rows).to_csv(args.output_dir / "uncovered_positions.csv", index=False)
    if crosswalk_parts:
        crosswalk_output = pd.concat(crosswalk_parts, ignore_index=True)
        if "MAPPING_VALIDATION_STATUS" not in crosswalk_output:
            crosswalk_output["MAPPING_VALIDATION_STATUS"] = "CANDIDATE_UNREVIEWED"
        else:
            crosswalk_output["MAPPING_VALIDATION_STATUS"] = crosswalk_output["MAPPING_VALIDATION_STATUS"].fillna("CANDIDATE_UNREVIEWED")
        crosswalk_output.to_csv(args.output_dir / "security_crosswalk.csv", index=False)
    else:
        pd.DataFrame(columns=["SECURITY_KEY", "TICKER_RESOLVED", "MAPPING_SOURCE", "RETURN_AVAILABLE"]).to_csv(
            args.output_dir / "security_crosswalk.csv", index=False
        )

    calculated = results[results["STATUS"] == "CALCULATED"].copy() if not results.empty else pd.DataFrame()
    aggregate = {
        "source_dataset": DATASET_REPO,
        "source_note": "Unofficial Hugging Face Parquet mirror of SEC public-domain Form N-PORT structured data; SEC remains authoritative.",
        "funds_in_sample_manifest": int(len(funds)),
        "report_date_window": {"start": args.start_date, "end": args.end_date},
        "observed_report_dates": sorted(selected["REPORT_DATE"].dropna().unique().tolist()),
        "source_partitions": args.partitions,
        "benchmark_series": args.benchmark_series,
        "benchmark_name": "iShares Core S&P 500 ETF (IVV) N-PORT holdings proxy",
        "expected_fund_intervals": int(len(results)), "observed_fund_intervals": int(len(results)),
        "strict_no_trade_intervals_calculated": int(len(calculated)),
        "identity_reviewed_intervals": 0,
        "return_coverage_definition": "All beginning equity positions have endpoint prices for a candidate ticker; security identity mappings have not yet received manual approval.",

        "intervals_withheld_for_incomplete_coverage": int((results.STATUS == "WITHHELD_INCOMPLETE_RETURN_COVERAGE").sum()) if not results.empty else 0,
        "missing_fund_or_benchmark_observations": int(results.STATUS.astype(str).str.contains("MISSING|GAP", regex=True).sum()) if not results.empty else 0,
        "mean_return_coverage": float(results.RETURN_COVERAGE_START_EQUITY_WEIGHT.mean()) if not results.empty and "RETURN_COVERAGE_START_EQUITY_WEIGHT" in results else None,
        "mean_actual_minus_no_trade_active_share": float(calculated.ACTUAL_MINUS_NO_TRADE_ACTIVE_SHARE.mean()) if not calculated.empty else None,
        "median_actual_minus_no_trade_active_share": float(calculated.ACTUAL_MINUS_NO_TRADE_ACTIVE_SHARE.median()) if not calculated.empty else None,
        "fraction_negative_actual_minus_no_trade": float((calculated.ACTUAL_MINUS_NO_TRADE_ACTIVE_SHARE < 0).mean()) if not calculated.empty else None,
        "asset_weighted_actual_minus_no_trade_active_share": None,
        "interpretation": "Negative means actual ending equity sleeve is closer to the IVV holdings proxy than return-drift-only no-trade weights. Descriptive, not causal.",
        "limitations": [
            "The cohort is selected from funds present in the latest 2026 Q3 public release and with large-cap labels/strategy evidence; it is not survivorship-bias-free or representative of the full active-fund universe.",
            "The cohort remains purposive and size-biased; historical funds that disappeared before the latest release are not included.",
            "Only common-equity (ASSET_CAT=EC) holdings are modeled; cash, derivatives, shorts and other asset classes are excluded from the equity-sleeve calculation.",
            "Fund flows are not allocated to securities; the equity-sleeve counterfactual assumes proportional treatment of flows.",
            "Yahoo adjusted prices and OpenFIGI mappings are public feasibility sources, not an institutional-grade security master.",
            "Foreign-listed positions, FX, mergers, delistings and corporate actions still require position-level validation.",
            "All security mappings remain candidate/unreviewed; complete endpoint-price coverage is not equivalent to identity validation.",
            "Raw adjusted endpoint prices and dates are retained in security_crosswalk.csv for manual review.",
            "IVV holdings are a tracker-fund proxy, not official S&P 500 index weights.",
        ],
    }
    if not calculated.empty:
        weights = pd.to_numeric(calculated.START_NET_ASSETS_USD, errors="coerce").fillna(0)
        if weights.sum() > 0:
            aggregate["asset_weighted_actual_minus_no_trade_active_share"] = float(
                (calculated.ACTUAL_MINUS_NO_TRADE_ACTIVE_SHARE * weights).sum() / weights.sum()
            )
    (args.output_dir / "panel_summary.json").write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    funds.to_csv(args.output_dir / "sample_funds.csv", index=False)
    print(json.dumps(aggregate, indent=2), flush=True)

if __name__ == "__main__":
    main()
