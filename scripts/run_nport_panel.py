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


def load_metadata(cache_dir: Path, partitions: list[tuple[int, int]], series_ids: set[str], dates: set[str]) -> pd.DataFrame:
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
        x = x[
            x["SUB_TYPE"].isin(["NPORT-P", "NPORT-P/A"])
            & x["SERIES_ID"].isin(series_ids)
            & x["REPORT_DATE"].isin(dates)
        ].copy()
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
    parser.add_argument("--dates", nargs="+", default=REPORT_DATES)
    parser.add_argument("--partitions", nargs="+", default=["2025Q4", "2026Q1", "2026Q2", "2026Q3"])
    parser.add_argument("--benchmark-series", default=BENCHMARK_SERIES)
    args = parser.parse_args()
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    partitions = [(int(token[:4]), int(token[-1])) for token in args.partitions]
    funds = pd.read_csv(args.funds, dtype=str).fillna("")
    fund_ids = set(funds["SERIES_ID"])
    all_series = fund_ids | {args.benchmark_series}
    dates = set(args.dates)

    print(f"Loading filing metadata from {DATASET_REPO}: {partitions}", flush=True)
    filings = load_metadata(args.cache_dir, partitions, all_series, dates)
    if filings.empty:
        raise ValueError("No filings found for selected sample and report dates")
    selected = filings.copy()
    selected.to_csv(args.output_dir / "filing_resolution.csv", index=False)

    expected = []
    for series_id in sorted(fund_ids):
        fund_name = funds.loc[funds.SERIES_ID == series_id, "FUND_NAME"].iloc[0]
        for date in args.dates:
            expected.append({"SERIES_ID": series_id, "FUND_NAME": fund_name, "REPORT_DATE": date})
    for date in args.dates:
        expected.append({"SERIES_ID": args.benchmark_series, "FUND_NAME": "IVV benchmark proxy", "REPORT_DATE": date})
    expected_df = pd.DataFrame(expected)
    availability = expected_df.merge(
        selected[["SERIES_ID", "REPORT_DATE", "ACCESSION_NUMBER", "FILING_DATE", "SUB_TYPE", "NET_ASSETS", "REGISTRANT_NAME", "FILING_COUNT"]],
        on=["SERIES_ID", "REPORT_DATE"], how="left", validate="one_to_one"
    )
    availability.to_csv(args.output_dir / "observation_availability.csv", index=False)
    missing_obs = availability[availability["ACCESSION_NUMBER"].isna()]
    if not missing_obs.empty:
        print(f"WARNING: {len(missing_obs)} expected fund/benchmark observations missing", flush=True)

    valid_accessions = set(availability["ACCESSION_NUMBER"].dropna().astype(str))
    selected_rows = selected[selected["ACCESSION_NUMBER"].astype(str).isin(valid_accessions)].copy()
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
    long_weights = pd.concat([
        frame.assign(SERIES_ID=key[0], REPORT_DATE=key[1]) for key, frame in portfolios.items()
    ], ignore_index=True)
    long_weights.to_parquet(args.output_dir / "portfolio_equity_weights.parquet", index=False)

    # Cross-check the June 2026 mirror extraction against the original SEC ZIP pilot.
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

    interval_pairs = list(zip(args.dates[:-1], args.dates[1:]))
    result_rows = []
    coverage_rows = []
    ticker_cache: dict[str, str] = {}
    for start_date, end_date in interval_pairs:
        start_frames = []
        for series_id in sorted(fund_ids):
            frame = portfolios.get((series_id, start_date))
            if frame is not None:
                start_frames.append(frame)
        if not start_frames:
            continue
        union = pd.concat(start_frames, ignore_index=True).drop_duplicates("SECURITY_KEY")
        print(f"Fetching returns for {len(union)} unique starting securities: {start_date} to {end_date}", flush=True)
        returns = pilot.fetch_returns(union, start_date, end_date, ticker_cache=ticker_cache)
        ticker_cache.update({str(r.SECURITY_KEY): str(r.TICKER_RESOLVED or "") for r in returns.itertuples()})
        returns.to_csv(args.output_dir / f"security_returns_{start_date}_{end_date}.csv", index=False)

        benchmark = portfolios.get((args.benchmark_series, end_date))
        for series_id in sorted(fund_ids):
            start = portfolios.get((series_id, start_date))
            actual = portfolios.get((series_id, end_date))
            meta0 = portfolio_meta.get((series_id, start_date))
            meta1 = portfolio_meta.get((series_id, end_date))
            if start is None or actual is None or benchmark is None:
                result_rows.append({
                    "SERIES_ID": series_id, "FUND_NAME": funds.loc[funds.SERIES_ID == series_id, "FUND_NAME"].iloc[0],
                    "START_DATE": start_date, "END_DATE": end_date, "STATUS": "MISSING_FUND_OR_BENCHMARK_OBSERVATION"
                })
                continue
            nt, coverage, missing_keys = strict_no_trade(start, returns)
            actual_as = pilot.active_share(actual, benchmark)
            no_trade_as = pilot.active_share(nt, benchmark) if nt is not None else None
            delta = actual_as - no_trade_as if no_trade_as is not None else None
            result_rows.append({
                "SERIES_ID": series_id,
                "FUND_NAME": funds.loc[funds.SERIES_ID == series_id, "FUND_NAME"].iloc[0],
                "STYLE": funds.loc[funds.SERIES_ID == series_id, "STYLE"].iloc[0],
                "START_DATE": start_date, "END_DATE": end_date,
                "START_ACCESSION": meta0["ACCESSION_NUMBER"], "END_ACCESSION": meta1["ACCESSION_NUMBER"],
                "START_NET_ASSETS_USD": float(meta0["NET_ASSETS"]), "END_NET_ASSETS_USD": float(meta1["NET_ASSETS"]),
                "START_EQUITY_PCT_NAV": float(meta0["EQUITY_PCT_NAV"]),
                "END_EQUITY_PCT_NAV": float(meta1["EQUITY_PCT_NAV"]),
                "START_EQUITY_POSITIONS": int(len(start)), "END_EQUITY_POSITIONS": int(len(actual)),
                "RETURN_COVERAGE_START_EQUITY_WEIGHT": coverage,
                "POSITIONS_MISSING_RETURN": int(len(missing_keys)),
                "STRICT_NO_TRADE_CALCULATED": nt is not None,
                "ACTUAL_END_ACTIVE_SHARE_VS_IVV": actual_as,
                "NO_TRADE_ACTIVE_SHARE_VS_IVV": no_trade_as,
                "ACTUAL_MINUS_NO_TRADE_ACTIVE_SHARE": delta,
                "STATUS": "CALCULATED" if nt is not None else "WITHHELD_INCOMPLETE_RETURN_COVERAGE",
            })
            if missing_keys:
                miss = start[start.SECURITY_KEY.isin(missing_keys)].copy()
                for rec in miss.to_dict("records"):
                    coverage_rows.append({
                        "SERIES_ID": series_id, "FUND_NAME": funds.loc[funds.SERIES_ID == series_id, "FUND_NAME"].iloc[0],
                        "START_DATE": start_date, "END_DATE": end_date, **rec
                    })
            if nt is not None:
                nt.assign(SERIES_ID=series_id, START_DATE=start_date, END_DATE=end_date).to_csv(
                    args.output_dir / f"no_trade_weights_{series_id}_{start_date}_{end_date}.csv", index=False
                )

    results = pd.DataFrame(result_rows)
    results.to_csv(args.output_dir / "fund_interval_results.csv", index=False)
    pd.DataFrame(coverage_rows).to_csv(args.output_dir / "uncovered_positions.csv", index=False)

    calculated = results[results["STATUS"] == "CALCULATED"].copy() if not results.empty else pd.DataFrame()
    aggregate = {
        "source_dataset": DATASET_REPO,
        "source_note": "Unofficial Hugging Face Parquet mirror of SEC public-domain Form N-PORT structured data; SEC remains authoritative.",
        "funds_in_sample_manifest": int(len(funds)),
        "report_dates": args.dates,
        "source_partitions": args.partitions,
        "benchmark_series": args.benchmark_series,
        "benchmark_name": "iShares Core S&P 500 ETF (IVV) N-PORT holdings proxy",
        "expected_fund_intervals": int(len(funds) * max(len(args.dates)-1, 0)),
        "observed_fund_intervals": int(len(results)),
        "strict_no_trade_intervals_calculated": int(len(calculated)),
        "intervals_withheld_for_incomplete_coverage": int((results.STATUS == "WITHHELD_INCOMPLETE_RETURN_COVERAGE").sum()) if not results.empty else 0,
        "missing_fund_or_benchmark_observations": int((results.STATUS == "MISSING_FUND_OR_BENCHMARK_OBSERVATION").sum()) if not results.empty else 0,
        "mean_return_coverage": float(results.RETURN_COVERAGE_START_EQUITY_WEIGHT.mean()) if not results.empty and "RETURN_COVERAGE_START_EQUITY_WEIGHT" in results else None,
        "mean_actual_minus_no_trade_active_share": float(calculated.ACTUAL_MINUS_NO_TRADE_ACTIVE_SHARE.mean()) if not calculated.empty else None,
        "median_actual_minus_no_trade_active_share": float(calculated.ACTUAL_MINUS_NO_TRADE_ACTIVE_SHARE.median()) if not calculated.empty else None,
        "fraction_negative_actual_minus_no_trade": float((calculated.ACTUAL_MINUS_NO_TRADE_ACTIVE_SHARE < 0).mean()) if not calculated.empty else None,
        "asset_weighted_actual_minus_no_trade_active_share": None,
        "interpretation": "Negative means actual ending equity sleeve is closer to the IVV holdings proxy than return-drift-only no-trade weights. Descriptive, not causal.",
        "limitations": [
            "The sample is selected from funds present in the latest 2026 Q3 public release and with large-cap labels/strategy evidence; it is not survivorship-bias-free or representative of the full active-fund universe.",
            "A balanced four-quarter sample can exclude entrants, liquidated funds, merged funds, and funds that changed names or strategies.",
            "Only common-equity (ASSET_CAT=EC) holdings are modeled; cash, derivatives, shorts and other asset classes are excluded from the equity-sleeve calculation.",
            "Fund flows are not allocated to securities; the equity-sleeve counterfactual assumes proportional treatment of flows.",
            "Yahoo adjusted prices and OpenFIGI mappings are public feasibility sources, not an institutional-grade security master.",
            "Foreign-listed positions, FX, mergers, delistings, ticker changes and corporate actions require position-level validation; strict no-trade results are withheld when any starting position lacks a return.",
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
