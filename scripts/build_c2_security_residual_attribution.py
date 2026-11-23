#!/usr/bin/env python3
"""Attribute the C.2 Active Share portfolio-change residual to individual securities."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from build_c2_no_trade_drift_pilot import security_identifier


def normalized_end_weights(holdings: pd.DataFrame, entity: str, end_date: str) -> tuple[dict[str, float], dict[str, str]]:
    subset = holdings[
        holdings["entity"].eq(entity)
        & holdings["report_date"].eq(end_date)
        & holdings["is_common_equity"].astype(str).str.lower().eq("true")
    ].copy()
    if subset.empty:
        raise ValueError(f"No end-date common-equity holdings for {entity} {end_date}")
    subset["weight_num"] = pd.to_numeric(subset["pct_net_assets"], errors="coerce").fillna(0.0)
    subset["security_id"] = subset.apply(lambda row: security_identifier(row.to_dict()), axis=1)
    grouped = subset.groupby("security_id", sort=True).agg(
        weight_num=("weight_num", "sum"),
        name=("name", "first"),
    )
    total = float(grouped["weight_num"].sum())
    if total <= 0:
        raise ValueError(f"Non-positive end-date common-equity weight for {entity}")
    weights = (grouped["weight_num"] / total).to_dict()
    names = grouped["name"].astype(str).to_dict()
    return weights, names


def flag_is_true(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def clean_flag(value: object) -> object:
    if pd.isna(value):
        return ""
    return value


def security_residual_contributions(
    actual_end: dict[str, float],
    no_trade_end: dict[str, float],
    benchmark_end: dict[str, float],
) -> dict[str, float]:
    """Additive per-security contribution to AS(actual, benchmark)-AS(no-trade, benchmark), in pp."""
    universe = set(actual_end) | set(no_trade_end) | set(benchmark_end)
    return {
        sid: 50.0 * (
            abs(actual_end.get(sid, 0.0) - benchmark_end.get(sid, 0.0))
            - abs(no_trade_end.get(sid, 0.0) - benchmark_end.get(sid, 0.0))
        )
        for sid in universe
    }


def build_attribution(
    holdings: pd.DataFrame,
    drift: pd.DataFrame,
    decompositions: pd.DataFrame,
    end_date: str,
    tolerance_pp: float = 1e-8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, summaries = [], []
    for decomposition in decompositions.to_dict("records"):
        if decomposition.get("calculation_status") != "calculated":
            continue
        fund = decomposition["fund"]
        benchmark = decomposition["benchmark_entity"]
        fund_rows = drift[drift["fund"].eq(fund)].copy()
        if fund_rows.empty:
            raise ValueError(f"No fund security-drift rows for {fund}")
        actual_end = dict(zip(
            fund_rows["security_id"],
            pd.to_numeric(fund_rows["actual_end_weight_pct_equity"], errors="raise") / 100.0,
        ))
        no_trade_end = dict(zip(
            fund_rows["security_id"],
            pd.to_numeric(fund_rows["no_trade_end_weight_pct_equity"], errors="raise") / 100.0,
        ))
        benchmark_end, benchmark_names = normalized_end_weights(holdings, benchmark, end_date)
        if abs(sum(actual_end.values()) - 1.0) > 1e-8:
            raise AssertionError(f"Actual end weights do not sum to one for {fund}")
        if abs(sum(no_trade_end.values()) - 1.0) > 1e-8:
            raise AssertionError(f"No-trade end weights do not sum to one for {fund}")
        fund_names = dict(zip(fund_rows["security_id"], fund_rows["name"]))
        contribution = security_residual_contributions(actual_end, no_trade_end, benchmark_end)
        target = float(decomposition["actual_portfolio_change_beyond_drift_pp"])
        observed = float(sum(contribution.values()))
        error = observed - target
        if abs(error) > tolerance_pp:
            raise AssertionError(
                f"Security attribution does not reconcile for {fund}/{benchmark}: "
                f"security sum={observed:.12f}, residual={target:.12f}, error={error:.12g} pp"
            )

        flag_columns = [
            "strategy_classification", "strategy_group", "manager_change_within_window",
            "manager_change_effective_date", "advisory_agreement_replaced_within_window",
            "advisory_agreement_change_effective_date", "manager_ownership_or_control_change_within_window",
            "day_to_day_portfolio_management_change_established", "published_aggregate_subadviser_allocation_stable",
            "non_diversified_status",
            "non_diversified_effective_date", "fee_limit_change_effective_date",
            "structural_change_flag_ids",
        ]
        flags = {key: clean_flag(decomposition.get(key, "")) for key in flag_columns}
        for key in ("manager_change_within_window", "advisory_agreement_replaced_within_window",
                    "manager_ownership_or_control_change_within_window",
                    "day_to_day_portfolio_management_change_established",
                    "published_aggregate_subadviser_allocation_stable", "non_diversified_status"):
            flags[key] = flag_is_true(flags.get(key, False))
        for sid, value in contribution.items():
            rows.append({
                "fund": fund,
                "benchmark_entity": benchmark,
                "security_id": sid,
                "security_name": fund_names.get(sid) or benchmark_names.get(sid, ""),
                "actual_end_weight_pct": 100.0 * actual_end.get(sid, 0.0),
                "no_trade_end_weight_pct": 100.0 * no_trade_end.get(sid, 0.0),
                "benchmark_end_weight_pct": 100.0 * benchmark_end.get(sid, 0.0),
                "actual_minus_no_trade_weight_pp": 100.0 * (
                    actual_end.get(sid, 0.0) - no_trade_end.get(sid, 0.0)
                ),
                "residual_contribution_pp": value,
                **flags,
            })
        frame = pd.DataFrame([
            {"security_id": sid, "security_name": fund_names.get(sid) or benchmark_names.get(sid, ""),
             "residual_contribution_pp": value}
            for sid, value in contribution.items()
        ])
        frame = frame[frame["residual_contribution_pp"].abs() > 1e-12].copy()
        positive = frame[frame["residual_contribution_pp"] > 0].sort_values(
            "residual_contribution_pp", ascending=False
        )
        negative = frame[frame["residual_contribution_pp"] < 0].sort_values(
            "residual_contribution_pp"
        )
        abs_total = float(frame["residual_contribution_pp"].abs().sum())
        top10_abs = float(frame.reindex(
            frame["residual_contribution_pp"].abs().sort_values(ascending=False).index
        ).head(10)["residual_contribution_pp"].abs().sum())
        summaries.append({
            "fund": fund,
            "benchmark_entity": benchmark,
            **flags,
            "security_count": int(len(frame)),
            "positive_contributions_sum_pp": float(positive["residual_contribution_pp"].sum()),
            "negative_contributions_sum_pp": float(negative["residual_contribution_pp"].sum()),
            "net_residual_pp": observed,
            "reported_residual_pp": target,
            "reconciliation_error_pp": error,
            "top10_absolute_contributions_share_pct": 100.0 * top10_abs / abs_total if abs_total else 0.0,
            "top5_positive": "; ".join(
                f"{r.security_name} ({r.residual_contribution_pp:+.3f} pp)"
                for r in positive.head(5).itertuples()
            ),
            "top5_negative": "; ".join(
                f"{r.security_name} ({r.residual_contribution_pp:+.3f} pp)"
                for r in negative.head(5).itertuples()
            ),
        })
    attribution = pd.DataFrame(rows).sort_values(
        ["fund", "benchmark_entity", "residual_contribution_pp"],
        ascending=[True, True, False],
    ).reset_index(drop=True)
    summary = pd.DataFrame(summaries).sort_values(
        ["fund", "benchmark_entity"]
    ).reset_index(drop=True)
    if len(summary) != len(decompositions[decompositions["calculation_status"].eq("calculated")]):
        raise AssertionError("Not every calculated fund/benchmark decomposition received attribution")
    return attribution, summary


def write_report(summary: pd.DataFrame, output: Path, end_date: str) -> None:
    lines = [
        "# C.2 Security-Level Attribution of the Active Share Residual",
        "",
        f"**End date:** {end_date}. **Scope:** every calculated fund/benchmark pair in the C.2 cohort.",
        "",
        "## Method",
        "",
        "For each security, the contribution to the portfolio-change residual is "
        "`50 × (|actual end weight − benchmark end weight| − |no-trade end weight − benchmark end weight|)`, "
        "in percentage points. Summing these contributions exactly reproduces "
        "`Active Share(actual fund end, benchmark end) − Active Share(no-trade fund end, benchmark end)`.",
        "",
        "Positive contributions increase the residual; negative contributions reduce it. "
        "The attribution is benchmark-relative and depends on the absolute-value geometry of Active Share. "
        "It is not a return attribution, a trading-volume measure, or evidence of manager intent. "
        "The same security can contribute differently against IWB and SPY.",
        "",
        "## Fund/benchmark summaries",
        "",
        "| Fund | Reviewed context | Benchmark | Securities | Positive sum (pp) | Negative sum (pp) | Net residual (pp) | Top 10 share of absolute contributions |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in summary.itertuples():
        context = str(r.strategy_classification or "")
        if flag_is_true(getattr(r, "advisory_agreement_replaced_within_window", False)):
            context += f"; DMC advisory agreement/ownership transition {r.advisory_agreement_change_effective_date}; sub-advisers continued, published split stable"
        elif flag_is_true(r.manager_change_within_window):
            context += f"; named manager change {r.manager_change_effective_date}"
        elif flag_is_true(r.non_diversified_status) and str(r.non_diversified_effective_date):
            context += f"; non-diversified since {r.non_diversified_effective_date}"
        elif str(r.fee_limit_change_effective_date):
            context += f"; R6 fee-limit change {r.fee_limit_change_effective_date}"
        lines.append(
            f"| {r.fund} | {context} | {r.benchmark_entity} | {r.security_count} | "
            f"{r.positive_contributions_sum_pp:+.3f} | {r.negative_contributions_sum_pp:+.3f} | "
            f"{r.net_residual_pp:+.3f} | {r.top10_absolute_contributions_share_pct:.1f}% |"
        )
    lines += [
        "",
        "## What stands out",
        "",
        "The residual sign agrees between IWB and SPY for all six funds. The security-level attribution also shows why a small net residual should not be mistaken for small underlying differences: positive and negative name-level contributions can be large and offset one another.",
        "",
        "Magellan's residual is only about +0.1 pp, while its gross positive and negative security contributions are each about 4.5 pp; its ten largest absolute name contributions account for roughly 56% of the total absolute contribution. JPMorgan Large Cap Value has gross positive and negative contributions near +14.8 and -15.8 pp, netting to about -1.0 pp. Contrafund and Optimum show more diffuse contributions, with top-ten absolute shares around 22% and 27%, respectively.",
        "",
        "The concentration statistic is the top-ten share of the sum of absolute security contributions, not the share of the net residual.",
        "",
        "## Largest positive and negative security contributions",
        "",
    ]
    for r in summary.itertuples():
        lines += [
            f"### {r.fund} — {r.benchmark_entity}",
            "",
            f"**Positive:** {r.top5_positive or 'None'}",
            "",
            f"**Negative:** {r.top5_negative or 'None'}",
            "",
            f"Reconciliation: security contributions {r.net_residual_pp:+.9f} pp; "
            f"reported residual {r.reported_residual_pp:+.9f} pp; "
            f"error {r.reconciliation_error_pp:+.3e} pp.",
            "",
        ]
    lines += [
        "## Interpretation cautions",
        "",
        "This is a security-level decomposition of the Active Share residual, not a causal explanation "
        "of why a fund held a security or changed its weight. N-PORT endpoint differences may reflect "
        "flows, corporate actions, cash/derivatives, reporting differences, and other effects. "
        "Keep each fund's reviewed strategy and structural flags attached to the results. "
        "In particular, Optimum's December 1, 2025 event was a DMC advisory-agreement replacement and ultimate-ownership/control change, not a change in the named investment manager; American Century and Los Angeles Capital continued and published aggregate sleeve allocations were stable. "
        "The two JPMorgan funds' non-diversified status changes predate the observation window; Oakmark's flag is a fee-limit change, not an identified strategy change.",
        "",
        "The full security-level rows are in `c2_cohort_security_residual_attribution.csv`; "
        "the machine-readable pair summaries are in `c2_cohort_security_residual_summary.csv`.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="c2_nport_cohort")
    parser.add_argument("--out", default="c2_nport_cohort")
    parser.add_argument("--end-date", default="2025-12-31")
    args = parser.parse_args()
    source, output = Path(args.input), Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    holdings = pd.read_csv(source / "nport_cohort_common_equity.csv", dtype=str).fillna("")
    drift = pd.read_csv(source / "c2_cohort_fund_security_drift.csv", dtype=str).fillna("")
    decompositions = pd.read_csv(source / "c2_cohort_active_share_decomposition.csv")
    attribution, summary = build_attribution(holdings, drift, decompositions, args.end_date)
    attribution.to_csv(output / "c2_cohort_security_residual_attribution.csv", index=False)
    summary.to_csv(output / "c2_cohort_security_residual_summary.csv", index=False)
    write_report(summary, output / "C2_COHORT_SECURITY_RESIDUAL_ATTRIBUTION.md", args.end_date)
    print(summary[[
        "fund", "benchmark_entity", "net_residual_pp", "reconciliation_error_pp",
        "top10_absolute_contributions_share_pct",
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
