#!/usr/bin/env python3
"""SEC N-PORT two-date pilot; public-data-only.

Optional returns path: free OpenFIGI mapping + Yahoo Finance adjusted prices.
This is a feasibility pipeline, not a complete survivorship-bias-free security master.
"""
import argparse, json, time, zipfile
from pathlib import Path
import pandas as pd

HOLDING_COLS = ["ACCESSION_NUMBER","HOLDING_ID","ISSUER_NAME","ISSUER_TITLE","ISSUER_CUSIP",
                "BALANCE","UNIT","CURRENCY_CODE","CURRENCY_VALUE","EXCHANGE_RATE","PERCENTAGE",
                "PAYOFF_PROFILE","ASSET_CAT","ISSUER_TYPE","INVESTMENT_COUNTRY"]
ID_COLS = ["HOLDING_ID","IDENTIFIERS_ID","IDENTIFIER_ISIN","IDENTIFIER_TICKER",
           "OTHER_IDENTIFIER","OTHER_IDENTIFIER_DESC"]

def read_table(zf, name):
    with zf.open(name + ".tsv") as f:
        return pd.read_csv(f, sep="\t", dtype=str, low_memory=False).fillna("")

def resolve_filings(zf):
    sub, info, reg = (read_table(zf,n) for n in ["SUBMISSION","FUND_REPORTED_INFO","REGISTRANT"])
    x = sub.merge(info,on="ACCESSION_NUMBER",validate="one_to_one")
    x = x.merge(reg[["ACCESSION_NUMBER","CIK","REGISTRANT_NAME"]],on="ACCESSION_NUMBER",validate="one_to_one")
    x["REPORT_DT"] = pd.to_datetime(x.REPORT_DATE,format="%d-%b-%Y",errors="coerce")
    x["FILING_DT"] = pd.to_datetime(x.FILING_DATE,format="%d-%b-%Y",errors="coerce")
    x["FUND_KEY"] = x.SERIES_ID.where(x.SERIES_ID.ne(""),
        "FALLBACK|"+x.CIK+"|"+x.SERIES_LEI+"|"+x.SERIES_NAME)
    x["SUBTYPE_RANK"] = x.SUB_TYPE.map({"NPORT-P":1,"NPORT-P/A":2}).fillna(0)
    x = x.sort_values(["FUND_KEY","REPORT_DT","FILING_DT","SUBTYPE_RANK","ACCESSION_NUMBER"])
    x["GROUP_FILINGS"] = x.groupby(["FUND_KEY","REPORT_DT"]).ACCESSION_NUMBER.transform("count")
    return x, x.drop_duplicates(["FUND_KEY","REPORT_DT"],keep="last").copy()

def extract_holdings(zf, accessions):
    parts=[]
    with zf.open("FUND_REPORTED_HOLDING.tsv") as f:
        for c in pd.read_csv(f,sep="\t",dtype=str,usecols=HOLDING_COLS,chunksize=200000):
            q=c[c.ACCESSION_NUMBER.isin(accessions)]
            if len(q): parts.append(q)
    if not parts: raise ValueError("No holdings found for selected accessions")
    h=pd.concat(parts,ignore_index=True).fillna("")
    wanted=set(h.HOLDING_ID); parts=[]
    with zf.open("IDENTIFIERS.tsv") as f:
        for c in pd.read_csv(f,sep="\t",dtype=str,usecols=ID_COLS,chunksize=300000):
            q=c[c.HOLDING_ID.isin(wanted)]
            if len(q): parts.append(q)
    ids=pd.concat(parts,ignore_index=True).fillna("") if parts else pd.DataFrame(columns=ID_COLS)
    bridge=[]
    for hid,g in ids.groupby("HOLDING_ID",sort=False):
        isin=sorted(set(v.strip() for v in g.IDENTIFIER_ISIN if v.strip()))
        tick=sorted(set(v.strip() for v in g.IDENTIFIER_TICKER if v.strip()))
        bridge.append({"HOLDING_ID":hid,"ISIN":isin[0] if len(isin)==1 else "",
                       "ISIN_COUNT":len(isin),"TICKER":tick[0] if len(tick)==1 else "",
                       "TICKER_COUNT":len(tick),"IDENTIFIER_ROWS":len(g)})
    h=h.merge(pd.DataFrame(bridge),on="HOLDING_ID",how="left",validate="one_to_one")
    h[["ISIN","TICKER"]]=h[["ISIN","TICKER"]].fillna("")
    h["PCT_NAV"]=pd.to_numeric(h.PERCENTAGE,errors="coerce")/100
    cusip=h.ISSUER_CUSIP.str.strip().ne("") & h.ISSUER_CUSIP.str.strip().ne("000000000")
    h["SECURITY_KEY"]=h.ISIN.where(h.ISIN.ne(""),h.ISSUER_CUSIP.where(cusip,"UNRESOLVED|"+h.HOLDING_ID))
    h["IDENTITY_STATUS"]="ISIN"
    h.loc[h.ISIN.eq("") & cusip,"IDENTITY_STATUS"]="CUSIP_FALLBACK"
    h.loc[h.SECURITY_KEY.str.startswith("UNRESOLVED|"),"IDENTITY_STATUS"]="UNRESOLVED"
    h.loc[h.ISIN_COUNT.fillna(0).astype(int).gt(1),"IDENTITY_STATUS"]="AMBIGUOUS_ISIN"
    return h

def equity_weights(h, accession):
    x=h[(h.ACCESSION_NUMBER==accession)&(h.ASSET_CAT=="EC")].copy()
    x=x[x.PCT_NAV.notna()]
    g=x.groupby("SECURITY_KEY",as_index=False).agg(
        PCT_NAV=("PCT_NAV","sum"),ISSUER_NAME=("ISSUER_NAME","first"),
        ISSUER_CUSIP=("ISSUER_CUSIP","first"),ISIN=("ISIN","first"),
        TICKER=("TICKER","first"),IDENTITY_STATUS=("IDENTITY_STATUS","first"),
        RAW_HOLDING_ROWS=("HOLDING_ID","count"))
    total=g.PCT_NAV.sum()
    g["EQUITY_WEIGHT"]=g.PCT_NAV/total if total else 0
    return g,total

def active_share(a,b):
    aa=a.set_index("SECURITY_KEY").EQUITY_WEIGHT
    bb=b.set_index("SECURITY_KEY").EQUITY_WEIGHT
    ix=aa.index.union(bb.index)
    return float(.5*(aa.reindex(ix,fill_value=0)-bb.reindex(ix,fill_value=0)).abs().sum())

def calculate_no_trade(start, returns):
    x=start[["SECURITY_KEY","EQUITY_WEIGHT"]].merge(
        returns[["SECURITY_KEY","RETURN"]],on="SECURITY_KEY",how="left",validate="one_to_one")
    coverage=float(x.loc[x.RETURN.notna(),"EQUITY_WEIGHT"].sum())
    if coverage < .999999: return None,coverage
    x["NT_RAW"]=x.EQUITY_WEIGHT*(1+x.RETURN)
    x["EQUITY_WEIGHT"]=x.NT_RAW/x.NT_RAW.sum()
    return x[["SECURITY_KEY","EQUITY_WEIGHT"]],coverage

def fetch_returns(start, start_date, end_date):
    import requests, yfinance as yf
    jobs=[]; keys=[]; mapping={}
    for r in start.to_dict("records"):
        if r["ISIN"]:
            jobs.append({"idType":"ID_ISIN","idValue":r["ISIN"],"exchCode":"US","includeUnlistedEquities":True})
            keys.append(r["SECURITY_KEY"])
        elif r["ISSUER_CUSIP"] and r["ISSUER_CUSIP"]!="000000000":
            jobs.append({"idType":"ID_CUSIP","idValue":r["ISSUER_CUSIP"],"exchCode":"US","includeUnlistedEquities":True})
            keys.append(r["SECURITY_KEY"])
        else: mapping[r["SECURITY_KEY"]]=""
    for i in range(0,len(jobs),10):
        res=requests.post("https://api.openfigi.com/v3/mapping",json=jobs[i:i+10],
                          headers={"Content-Type":"application/json"},timeout=45)
        res.raise_for_status()
        for key,item in zip(keys[i:i+10],res.json()):
            data=item.get("data",[])
            good=[d for d in data if d.get("exchCode")=="US" and
                  ("common stock" in (d.get("securityType","")+" "+d.get("securityType2","")).lower()
                   or "depositary receipt" in (d.get("securityType","")+" "+d.get("securityType2","")).lower())]
            ts=sorted(set(d.get("ticker","") for d in good if d.get("ticker")))
            mapping[key]=ts[0].replace(".","-").replace("/","-") if len(ts)==1 else ""
        time.sleep(2.5)
    tickers=sorted(set(t for t in mapping.values() if t))
    if not tickers: return pd.DataFrame(columns=["SECURITY_KEY","RETURN","TICKER_RESOLVED"])
    try:
        px=yf.download(sorted(set(tickers+["SPY"])),
            start=(pd.Timestamp(start_date)-pd.Timedelta(days=10)).strftime("%Y-%m-%d"),
            end=(pd.Timestamp(end_date)+pd.Timedelta(days=5)).strftime("%Y-%m-%d"),
            auto_adjust=True,actions=True,progress=False,group_by="ticker",threads=True)
        def close(sym):
            return (px[(sym,"Close")] if isinstance(px.columns,pd.MultiIndex) else px["Close"]).dropna()
        cal=close("SPY")
    except Exception:
        return pd.DataFrame([{"SECURITY_KEY":k,"RETURN":None,"TICKER_RESOLVED":v} for k,v in mapping.items()])
    sd=cal.index[cal.index.date<=pd.Timestamp(start_date).date()]
    ed=cal.index[cal.index.date<=pd.Timestamp(end_date).date()]
    sdate=sd[-1] if len(sd) else None; edate=ed[-1] if len(ed) else None
    out=[]
    for key,ticker in mapping.items():
        value=None
        if ticker and sdate is not None and edate is not None:
            try:
                p=close(ticker)
                if sdate in p.index and edate in p.index: value=float(p.loc[edate]/p.loc[sdate]-1)
            except Exception: pass
        out.append({"SECURITY_KEY":key,"RETURN":value,"TICKER_RESOLVED":ticker,
                    "START_PRICE_DATE":str(sdate.date()) if sdate is not None else "",
                    "END_PRICE_DATE":str(edate.date()) if edate is not None else ""})
    return pd.DataFrame(out)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",required=True,type=Path)
    p.add_argument("--active-series",default="S000010411")
    p.add_argument("--benchmark-series",default="S000004310")
    p.add_argument("--start-date",default="2026-05-31")
    p.add_argument("--end-date",default="2026-06-30")
    p.add_argument("--fetch-returns",action="store_true")
    p.add_argument("--output-dir",type=Path,default=Path("data/nport_pilot"))
    a=p.parse_args(); a.output_dir.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.archive) as z:
        allf,resolved=resolve_filings(z)
        sd=pd.Timestamp(a.start_date); ed=pd.Timestamp(a.end_date)
        def select(series,date):
            q=resolved[(resolved.SERIES_ID==series)&(resolved.REPORT_DT==date)]
            if len(q)!=1: raise ValueError(f"Expected one filing for {series} at {date.date()}, got {len(q)}")
            return q.iloc[0]
        f0=select(a.active_series,sd); f1=select(a.active_series,ed); fb=select(a.benchmark_series,ed)
        acc=[f0.ACCESSION_NUMBER,f1.ACCESSION_NUMBER,fb.ACCESSION_NUMBER]
        h=extract_holdings(z,acc)
    h.to_csv(a.output_dir/"selected_raw_holdings.csv",index=False)
    allf[allf.SERIES_ID.isin([a.active_series,a.benchmark_series])].to_csv(
        a.output_dir/"filing_resolution_audit.csv",index=False)
    p0,w0=equity_weights(h,f0.ACCESSION_NUMBER)
    p1,w1=equity_weights(h,f1.ACCESSION_NUMBER)
    b1,wb=equity_weights(h,fb.ACCESSION_NUMBER)
    actual_as=active_share(p1,b1)
    common=len(set(p1.SECURITY_KEY)&set(b1.SECURITY_KEY))
    coverage=nt_as=trade_diff=None
    if a.fetch_returns:
        ret=fetch_returns(p0,sd,ed)
        ret.to_csv(a.output_dir/"security_returns.csv",index=False)
        nt,coverage=calculate_no_trade(p0,ret)
        if nt is not None:
            nt_as=active_share(nt,b1); trade_diff=actual_as-nt_as
            nt.to_csv(a.output_dir/"no_trade_end_equity_weights.csv",index=False)
    summary={
      "source_archive":a.archive.name,"active_fund":f1.SERIES_NAME,"active_series_id":a.active_series,
      "active_start_report_date":a.start_date,"active_end_report_date":a.end_date,
      "active_start_accession":f0.ACCESSION_NUMBER,"active_end_accession":f1.ACCESSION_NUMBER,
      "active_start_filing_date":f0.FILING_DATE,"active_end_filing_date":f1.FILING_DATE,
      "active_start_filing_type":f0.SUB_TYPE,"active_end_filing_type":f1.SUB_TYPE,
      "active_start_net_assets_usd":float(f0.NET_ASSETS),"active_end_net_assets_usd":float(f1.NET_ASSETS),
      "active_start_filing_group_count":int(f0.GROUP_FILINGS),"active_end_filing_group_count":int(f1.GROUP_FILINGS),
      "benchmark":fb.SERIES_NAME,"benchmark_series_id":a.benchmark_series,
      "benchmark_report_date":a.end_date,"benchmark_accession":fb.ACCESSION_NUMBER,
      "benchmark_filing_date":fb.FILING_DATE,"benchmark_filing_type":fb.SUB_TYPE,
      "benchmark_net_assets_usd":float(fb.NET_ASSETS),
      "active_start_all_holdings_pct_nav":float(pd.to_numeric(h.loc[h.ACCESSION_NUMBER==f0.ACCESSION_NUMBER,"PERCENTAGE"],errors="coerce").sum()),
      "active_end_all_holdings_pct_nav":float(pd.to_numeric(h.loc[h.ACCESSION_NUMBER==f1.ACCESSION_NUMBER,"PERCENTAGE"],errors="coerce").sum()),
      "benchmark_all_holdings_pct_nav":float(pd.to_numeric(h.loc[h.ACCESSION_NUMBER==fb.ACCESSION_NUMBER,"PERCENTAGE"],errors="coerce").sum()),
      "active_start_equity_holding_count":len(p0),"active_end_equity_holding_count":len(p1),
      "benchmark_equity_holding_count":len(b1),"active_start_equity_pct_nav":w0*100,
      "active_end_equity_pct_nav":w1*100,"benchmark_equity_pct_nav":wb*100,
      "active_actual_vs_tracker_equity_sleeve_active_share":actual_as,
      "shared_security_count":common,"active_end_unmatched_security_count":len(set(p1.SECURITY_KEY)-set(b1.SECURITY_KEY)),
      "benchmark_unmatched_security_count":len(set(b1.SECURITY_KEY)-set(p1.SECURITY_KEY)),
      "return_coverage_start_equity_weight":coverage,"no_trade_active_share":nt_as,
      "actual_minus_no_trade_active_share":trade_diff,
      "limitations":["No-trade estimate is omitted unless every beginning equity position has a return.",
        "OpenFIGI and Yahoo adjusted prices are public feasibility sources, not a complete survivorship-bias-free security master.",
        "Foreign listings, FX conversion, delistings, mergers and corporate actions need validation.",
        "Equity sleeve is normalized separately; cash, derivatives and non-equity positions remain in raw data but are excluded.",
        "Fund flows are not allocated to securities; equity-sleeve no-trade assumes proportional flow treatment.",
        "IVV holdings are a tracker-fund proxy, not official S&P 500 index weights."]}
    (a.output_dir/"pilot_summary.json").write_text(json.dumps(summary,indent=2))
    p1.assign(PORTFOLIO="ACTIVE_END").to_csv(a.output_dir/"active_end_equity_weights.csv",index=False)
    b1.assign(PORTFOLIO="TRACKER_END").to_csv(a.output_dir/"tracker_end_equity_weights.csv",index=False)
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
