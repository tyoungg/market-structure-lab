#!/usr/bin/env python3
"""Reproduce Optimum's three-filing holdings comparison and allocation history."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
FUND="Optimum Large Cap Growth Fund"
DATES=["2025-06-30","2025-09-30","2025-12-31"]

def security_key(row):
    for field,prefix in (("cusip","CUSIP"),("isin","ISIN")):
        value=str(row.get(field,"") or "").strip()
        if value and value.lower()!="nan": return f"{prefix}:{value}"
    ticker=str(row.get("ticker","") or "").strip()
    name=str(row.get("name","") or "").strip()
    if ticker and ticker.lower()!="nan": return f"TICKER:{ticker}|{name}"
    if name and name.lower()!="nan": return f"NAME:{name}"
    raise ValueError("Common-equity position lacks CUSIP, ISIN, ticker, and name")

def read_allocations(path):
    frame=pd.read_csv(path,dtype=str).fillna("")
    required={"report_date","american_century_pct","delaware_management_company_pct","los_angeles_capital_pct"}
    if not required.issubset(frame.columns): raise ValueError(f"Allocation file missing columns: {sorted(required-set(frame.columns))}")
    frame["report_date"]=frame["report_date"].astype(str)
    for col in required-{"report_date"}: frame[col]=pd.to_numeric(frame[col],errors="raise")
    if frame["report_date"].duplicated().any(): raise ValueError("Duplicate allocation report dates")
    months={"2025-09-30","2025-10-31","2025-11-30","2025-12-31"}
    if not months.issubset(set(frame["report_date"])): raise ValueError("Allocation history must include Sep, Oct, Nov, and Dec 2025 month-ends")
    totals=frame[["american_century_pct","delaware_management_company_pct","los_angeles_capital_pct"]].sum(axis=1)
    if not ((totals-100).abs()<=0.02).all(): raise ValueError("Published sub-adviser allocations do not sum to 100% within rounding tolerance")
    return frame.sort_values("report_date")

def build(input_csv,allocation_csv,out):
    raw=pd.read_csv(input_csv,dtype=str).fillna("")
    required={"entity","report_date","name","cusip","isin","ticker","pct_net_assets"}
    if not required.issubset(raw.columns): raise ValueError(f"N-PORT common-equity file missing columns: {sorted(required-set(raw.columns))}")
    rows=raw.loc[(raw["entity"]==FUND)&raw["report_date"].isin(DATES)].copy()
    if set(rows["report_date"].unique())!=set(DATES): raise ValueError(f"Expected Optimum filings for exactly {DATES}; found {sorted(rows['report_date'].unique())}")
    rows["pct_net_assets"]=pd.to_numeric(rows["pct_net_assets"],errors="raise")
    rows["security_key"]=rows.apply(security_key,axis=1)
    portfolios={}; summary=[]
    for date in DATES:
        subset=rows.loc[rows["report_date"]==date]
        grouped=subset.groupby("security_key",as_index=False).agg(name=("name","first"),ticker=("ticker","first"),cusip=("cusip","first"),isin=("isin","first"),weight_pct_nav=("pct_net_assets","sum"))
        equity_total=float(grouped["weight_pct_nav"].sum())
        if equity_total<=0: raise ValueError(f"Non-positive common-equity sleeve for {date}")
        grouped["weight_pct_equity"]=grouped["weight_pct_nav"]/equity_total*100.0
        grouped["report_date"]=date; portfolios[date]=grouped
        ranked=grouped["weight_pct_equity"].sort_values(ascending=False)
        summary.append({"report_date":date,"nport_common_equity_rows":int(len(subset)),"unique_securities":int(grouped["security_key"].nunique()),"common_equity_pct_net_assets":equity_total,"top_5_pct_equity":float(ranked.head(5).sum()),"top_10_pct_equity":float(ranked.head(10).sum()),"top_20_pct_equity":float(ranked.head(20).sum())})
    changes=[]; intervals=[]
    for start,end in zip(DATES[:-1],DATES[1:]):
        a=portfolios[start].set_index("security_key"); b=portfolios[end].set_index("security_key"); records=[]
        for key in sorted(set(a.index)|set(b.index)):
            ar=a.loc[key] if key in a.index else None; br=b.loc[key] if key in b.index else None
            aw=float(ar["weight_pct_equity"]) if ar is not None else 0.0
            bw=float(br["weight_pct_equity"]) if br is not None else 0.0
            rec={"start_date":start,"end_date":end,"security_key":key,"name":str(br["name"] if br is not None else ar["name"]),"ticker":str(br["ticker"] if br is not None else ar["ticker"]),"cusip":str(br["cusip"] if br is not None else ar["cusip"]),"isin":str(br["isin"] if br is not None else ar["isin"]),"start_weight_pct_equity":aw,"end_weight_pct_equity":bw,"weight_change_pp":bw-aw,"status":"continuing" if ar is not None and br is not None else ("added_at_end_date" if br is not None else "absent_at_end_date")}
            records.append(rec); changes.append(rec)
        intervals.append({"start_date":start,"end_date":end,"continuing_securities":sum(x["status"]=="continuing" for x in records),"added_at_end_date":sum(x["status"]=="added_at_end_date" for x in records),"absent_at_end_date":sum(x["status"]=="absent_at_end_date" for x in records),"one_way_composition_distance_pp":sum(abs(x["weight_change_pp"]) for x in records)/2.0})
    alloc=read_allocations(allocation_csv)
    selected=alloc.loc[alloc["report_date"].isin(["2025-09-30","2025-10-31","2025-11-30","2025-12-31"])].copy()
    sep=selected.loc[selected.report_date=="2025-09-30"].iloc[0]; dec=selected.loc[selected.report_date=="2025-12-31"].iloc[0]
    alloc_change={"american_century_change_sep_to_dec_pp":float(dec.american_century_pct-sep.american_century_pct),"los_angeles_capital_change_sep_to_dec_pp":float(dec.los_angeles_capital_pct-sep.los_angeles_capital_pct),"delaware_management_company_change_sep_to_dec_pp":float(dec.delaware_management_company_pct-sep.delaware_management_company_pct)}
    out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(summary).to_csv(out/"optimum_three_filing_summary.csv",index=False)
    pd.DataFrame(intervals).to_csv(out/"optimum_three_filing_interval_summary.csv",index=False)
    pd.DataFrame(changes).to_csv(out/"optimum_three_filing_security_changes.csv",index=False)
    selected.to_csv(out/"optimum_subadviser_allocation_history.csv",index=False)
    fmt=lambda x:f"{x:.2f}"
    lines=["# Optimum Large Cap Growth: Three-Filing Holdings and Sub-Adviser Allocation Review","",
    "**Filings:** 2025-06-30, 2025-09-30, and 2025-12-31. **Transition effective date:** 2025-12-01.",
    "**Scope:** common-equity positions from the frozen C.2 N-PORT cohort; weights are normalized to each date's common-equity sleeve.","",
    "## Three filing snapshots","","| Filing date | Common-equity rows | Unique securities | Equity sleeve (% NAV) | Top 5 (% equity) | Top 10 (% equity) | Top 20 (% equity) |","|---|---:|---:|---:|---:|---:|---:|"]
    for r in summary: lines.append(f"| {r['report_date']} | {r['nport_common_equity_rows']} | {r['unique_securities']} | {fmt(r['common_equity_pct_net_assets'])} | {fmt(r['top_5_pct_equity'])} | {fmt(r['top_10_pct_equity'])} | {fmt(r['top_20_pct_equity'])} |")
    lines += ["","## Endpoint-to-endpoint holdings comparison","","| Interval | Continuing securities | Added at later snapshot | Absent at later snapshot | One-way composition distance (pp) |","|---|---:|---:|---:|---:|"]
    for r in intervals: lines.append(f"| {r['start_date']} → {r['end_date']} | {r['continuing_securities']} | {r['added_at_end_date']} | {r['absent_at_end_date']} | {fmt(r['one_way_composition_distance_pp'])} |")
    lines += ["","The composition-distance measure is one-half the sum of absolute security-weight changes after normalizing each filing to its common-equity sleeve. It is not portfolio turnover: price movements, flows, corporate actions, and other events can change weights without corresponding trades. Added/absent means only present/absent at the two filing dates.","","### Largest September-to-December weight changes","","| Security | September weight (% equity) | December weight (% equity) | Change (pp) |","|---|---:|---:|---:|"]
    for r in sorted([x for x in changes if x["start_date"]=="2025-09-30"],key=lambda x:abs(x["weight_change_pp"]),reverse=True)[:12]: lines.append(f"| {r['name']} ({r['ticker'] or r['security_key']}) | {fmt(r['start_weight_pct_equity'])} | {fmt(r['end_weight_pct_equity'])} | {r['weight_change_pp']:+.2f} |")
    lines += ["","## Official monthly sub-adviser allocation history","","| Month-end | American Century (%) | Delaware Management Company (%) | Los Angeles Capital (%) |","|---|---:|---:|---:|"]
    for _,r in selected.iterrows(): lines.append(f"| {r['report_date']} | {fmt(r['american_century_pct'])} | {fmt(r['delaware_management_company_pct'])} | {fmt(r['los_angeles_capital_pct'])} |")
    lines += ["",f"From September 30 to December 31, the published American Century allocation changed by {alloc_change['american_century_change_sep_to_dec_pp']:+.2f} pp and Los Angeles Capital by {alloc_change['los_angeles_capital_change_sep_to_dec_pp']:+.2f} pp. The DMC sub-adviser allocation remained {fmt(float(dec.delaware_management_company_pct))}% (DMC is the investment manager, not one of the two continuing sub-advisers).","","## Legal and management interpretation","","The December 9, 2025 SEC information statement identifies Delaware Management Company (DMC) as the Fund's investment manager. DMC became a series of Nomura Investment Management Business Trust following Nomura's acquisition of Macquarie's U.S. and European public asset-management business. The acquisition automatically terminated the prior advisory agreement; a new DMC investment advisory agreement became effective December 1, 2025. American Century and Los Angeles Capital were approved to continue as sub-advisers under new agreements effective the same date.","","Accordingly, this is an ownership/control and advisory-agreement transition, not a change in the named investment manager from DMC to Nomura. The three N-PORT filings show aggregate fund holdings, not which sub-adviser managed each security or when trades occurred. The published allocation series shows continuity in the aggregate division of assets between the two sub-advisers; it does not prove that their security-level decisions, personnel, processes, or sleeve holdings were unchanged.","","## What the filings do not establish","","- They do not identify security-level holdings by sub-adviser.","- They do not show trade dates, trade direction, quantities bought/sold between reporting dates, or the decision-maker.","- They do not distinguish active trades from market moves, fund flows, corporate actions, or other portfolio effects.","- They do not establish that the ownership/advisory-agreement transition caused any holdings change, or that day-to-day portfolio management changed or did not change.","- December 31 is a month-end snapshot 30 days after the effective date, not a clean daily record of the post-transition portfolio.","","## Sources and reproducibility","","- SEC definitive information statement, filed December 9, 2025: https://www.sec.gov/Archives/edgar/data/1227523/000207184425000626/optimum12092025def14c.htm.","- Official Optimum fund page and allocation history: https://www.optimummutualfunds.com/products/optimum-large-cap-growth-fund (retrieved 2026-11-23; allocations include securities, cash, and other assets managed in each sub-adviser sleeve).","- Input holdings: nport_cohort_common_equity.csv from the validated C.2 cohort acquisition run.","- Allocation input: research/OPTIMUM_SUBADVISER_ALLOCATIONS_2025.csv.","- Regeneration: scripts/audit_optimum_manager_transition.py.",""]
    (out/"OPTIMUM_THREE_FILING_TRANSITION_AUDIT.md").write_text("\n".join(lines),encoding="utf-8")
    return {"filing_summary":summary,"interval_summary":intervals,"allocation_change":alloc_change}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default="c2_nport_cohort")
    parser.add_argument("--out",default="c2_nport_cohort")
    parser.add_argument("--allocations",default="research/OPTIMUM_SUBADVISER_ALLOCATIONS_2025.csv")
    args=parser.parse_args()
    print(build(Path(args.input)/"nport_cohort_common_equity.csv",Path(args.allocations),Path(args.out)))

if __name__=="__main__": main()
