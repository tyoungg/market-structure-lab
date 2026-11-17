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

def select_latest_valid_filings(x):
    """Exclude late-filing notices; latest valid NPORT-P/A or NPORT-P wins."""
    valid = x[x.SUB_TYPE.isin(["NPORT-P","NPORT-P/A"])].copy()
    valid["SUBTYPE_RANK"] = valid.SUB_TYPE.map({"NPORT-P":1,"NPORT-P/A":2})
    valid = valid.sort_values(["FUND_KEY","REPORT_DT","FILING_DT","SUBTYPE_RANK","ACCESSION_NUMBER"])
    valid["GROUP_FILINGS"] = valid.groupby(["FUND_KEY","REPORT_DT"]).ACCESSION_NUMBER.transform("count")
    resolved = valid.drop_duplicates(["FUND_KEY","REPORT_DT"],keep="last").copy()
    return valid, resolved

def resolve_filings(zf):
    sub, info, reg = (read_table(zf,n) for n in ["SUBMISSION","FUND_REPORTED_INFO","REGISTRANT"])
    x = sub.merge(info,on="ACCESSION_NUMBER",validate="one_to_one")
    x = x.merge(reg[["ACCESSION_NUMBER","CIK","REGISTRANT_NAME"]],on="ACCESSION_NUMBER",validate="one_to_one")
    x["REPORT_DT"] = pd.to_datetime(x.REPORT_DATE,format="%d-%b-%Y",errors="coerce")
    x["FILING_DT"] = pd.to_datetime(x.FILING_DATE,format="%d-%b-%Y",errors="coerce")
    x["FUND_KEY"] = x.SERIES_ID.where(x.SERIES_ID.ne(""),
        "FALLBACK|"+x.CIK+"|"+x.SERIES_LEI+"|"+x.SERIES_NAME)
    valid, resolved = select_latest_valid_filings(x)
    counts = valid[["ACCESSION_NUMBER","GROUP_FILINGS"]]
    x = x.merge(counts,on="ACCESSION_NUMBER",how="left",validate="one_to_one")
    return x, resolved

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

def extract_close_series(prices, ticker):
    """Return adjusted Close regardless of yfinance MultiIndex column order."""
    if isinstance(prices.columns, pd.MultiIndex):
        for key in ((ticker, "Close"), ("Close", ticker)):
            if key in prices.columns:
                return prices.loc[:, key].dropna()
        raise KeyError(f"No Close column found for {ticker}; columns={list(prices.columns)[:8]}")
    if "Close" in prices.columns:
        return prices["Close"].dropna()
    raise KeyError(f"No Close column found for {ticker}")


def fetch_returns(start, start_date, end_date, ticker_cache=None):
    import re
    import requests, yfinance as yf
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()
    retry = Retry(total=5, connect=5, read=3, status=5, backoff_factor=2,
                  status_forcelist=[429,500,502,503,504],
                  allowed_methods=frozenset(["POST"]),
                  respect_retry_after_header=True)
    session.mount("https://", HTTPAdapter(max_retries=retry))

    rows = {r["SECURITY_KEY"]: r for r in start.to_dict("records")}
    ticker_cache = ticker_cache or {}
    mapping = {key: str(ticker_cache.get(key, "") or "") for key in rows}
    mapping_source = {key: ("prior_run_cache" if mapping[key] else "") for key in rows}
    mapping_details = {key: ({"ticker_cache": True} if mapping[key] else {}) for key in rows}

    # Use the ticker reported by N-PORT as a documented candidate before
    # external symbology lookup. A ticker candidate is not, by itself,
    # proof of a valid historical security match.
    for key, row in rows.items():
        nport_ticker = str(row.get("TICKER", "") or "").strip().upper()
        if not mapping[key] and nport_ticker:
            mapping[key] = nport_ticker.replace("/", "-").replace(".", "-")
            mapping_source[key] = "nport_reported_ticker"
            mapping_details[key]["nport_ticker_candidate"] = nport_ticker

    def norm_name(value):
        return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())

    def choose_ticker(good, issuer_name):
        candidates = []
        for d in good:
            raw = str(d.get("ticker", "")).strip().upper()
            yahoo = raw.replace("/", "-").replace(".", "-")
            # Avoid non-symbol codes and special when-issued/warrant lines.
            if not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,5}", yahoo):
                continue
            name = str(d.get("name", ""))
            upper_name = name.upper()
            if any(flag in upper_name for flag in ("W/D", "WHEN ISSUED", "WARRANT", "RIGHT")):
                continue
            candidates.append((yahoo, d))
        exact = [item for item in candidates
                 if norm_name(item[1].get("name", "")) == norm_name(issuer_name)]
        pool = exact if exact else candidates
        tickers = sorted(set(t for t, _ in pool))
        return tickers[0] if len(tickers) == 1 else ""

    def map_jobs(job_rows, source):
        for i in range(0, len(job_rows), 10):
            batch = job_rows[i:i+10]
            res = session.post(
                "https://api.openfigi.com/v3/mapping", json=[j[1] for j in batch],
                headers={"Content-Type": "application/json"}, timeout=45
            )
            res.raise_for_status()
            for (key, _), item in zip(batch, res.json()):
                data = item.get("data", [])
                good = [d for d in data if d.get("exchCode") == "US" and
                        ("common stock" in (d.get("securityType", "") + " " + d.get("securityType2", "")).lower()
                         or "depositary receipt" in (d.get("securityType", "") + " " + d.get("securityType2", "")).lower())]
                chosen = choose_ticker(good, rows[key].get("ISSUER_NAME", ""))
                mapping_details[key][source] = {
                    "chosen_ticker": chosen,
                    "figi_candidates": [
                        {"ticker": d.get("ticker", ""), "name": d.get("name", ""),
                         "figi": d.get("figi", ""), "securityType": d.get("securityType", ""),
                         "securityType2": d.get("securityType2", ""), "exchCode": d.get("exchCode", "")}
                        for d in good
                    ],
                    "mapping_error": item.get("error", "")
                }
                if chosen and not mapping[key]:
                    mapping[key] = chosen
                    mapping_source[key] = source
            time.sleep(2.5)

    # First pass: ISIN mapping.
    isin_jobs = []
    for key, row in rows.items():
        isin = str(row.get("ISIN", "")).strip()
        if isin and not mapping[key]:
            isin_jobs.append((key, {"idType": "ID_ISIN", "idValue": isin,
                                    "exchCode": "US", "includeUnlistedEquities": True}))
    map_jobs(isin_jobs, "isin")

    # Second pass: CUSIP fallback for every unresolved/ambiguous ISIN.
    cusip_jobs = []
    for key, row in rows.items():
        cusip = str(row.get("ISSUER_CUSIP", "")).strip()
        if not mapping[key] and cusip and cusip != "000000000":
            cusip_jobs.append((key, {"idType": "ID_CUSIP", "idValue": cusip,
                                     "exchCode": "US", "includeUnlistedEquities": True}))
    map_jobs(cusip_jobs, "cusip_fallback")

    # Explicit, source-documented overrides for identifiers OpenFIGI fails to resolve
    # or maps to a non-trading vendor code. Overrides supply symbols only; prices
    # are still fetched from Yahoo and must exist on both required dates.
    override_path = Path(__file__).resolve().parents[1] / "data" / "nport_pilot_inputs" / "ticker_overrides.csv"
    if override_path.exists():
        overrides = pd.read_csv(override_path, dtype=str).fillna("")
        for item in overrides.to_dict("records"):
            key = item.get("SECURITY_KEY", "")
            ticker = item.get("TICKER", "").strip().upper()
            if key in mapping and ticker and not mapping[key]:
                mapping[key] = ticker
                mapping_source[key] = "documented_manual_override"
                mapping_details[key]["manual_override"] = {
                    "ticker": ticker, "source_url": item.get("SOURCE_URL", ""),
                    "source_note": item.get("SOURCE_NOTE", "")
                }

    tickers = sorted(set(t for t in mapping.values() if t))
    if not tickers:
        return pd.DataFrame([{"SECURITY_KEY": k, "RETURN": None, "TICKER_RESOLVED": mapping[k],
                              "MAPPING_SOURCE": mapping_source[k],
                              "NPORT_TICKER": str(rows[k].get("TICKER", "") or ""),
                              "ISSUER_NAME": str(rows[k].get("ISSUER_NAME", "") or ""),
                              "ISIN": str(rows[k].get("ISIN", "") or ""),
                              "ISSUER_CUSIP": str(rows[k].get("ISSUER_CUSIP", "") or ""),
                              "FIGI_CANDIDATES": json.dumps(mapping_details[k], sort_keys=True),
                              "MAPPING_ERROR": ""} for k in rows])

    price_series = {}
    cal = None
    price_start = (pd.Timestamp(start_date) - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
    price_end = (pd.Timestamp(end_date) + pd.Timedelta(days=5)).strftime("%Y-%m-%d")
    # Keep requests serial to avoid yfinance's shared SQLite timezone-cache lock;
    # download manageable batches so a large cross-fund union does not become one fragile request.
    for offset in range(0, len(tickers), 40):
        batch = tickers[offset:offset + 40]
        symbols = list(batch)
        if offset == 0 and "SPY" not in symbols:
            symbols.append("SPY")
        try:
            px = yf.download(
                symbols, start=price_start, end=price_end,
                auto_adjust=True, actions=True, progress=False, group_by="ticker",
                threads=False, timeout=30
            )
            for symbol in batch:
                try:
                    price_series[symbol] = extract_close_series(px, symbol)
                except Exception as exc:
                    print(f"No usable Yahoo Close for {symbol}: {type(exc).__name__}: {exc}")
                    price_series[symbol] = pd.Series(dtype=float)
            if offset == 0:
                try:
                    cal = extract_close_series(px, "SPY")
                except Exception:
                    cal = None
        except Exception as exc:
            print(f"Price batch failed ({batch[0]}..{batch[-1]}): {type(exc).__name__}: {exc}")
            for symbol in batch:
                price_series[symbol] = pd.Series(dtype=float)

    if cal is None or cal.empty:
        try:
            spy = yf.download(
                ["SPY"], start=price_start, end=price_end,
                auto_adjust=True, actions=True, progress=False, group_by="ticker",
                threads=False, timeout=30
            )
            cal = extract_close_series(spy, "SPY")
        except Exception as exc:
            print(f"SPY calendar download failed: {type(exc).__name__}: {exc}")
            cal = pd.Series(dtype=float)

    if cal.empty:
        return pd.DataFrame([
            {"SECURITY_KEY": k, "RETURN": None, "TICKER_RESOLVED": v,
             "MAPPING_SOURCE": mapping_source[k],
             "NPORT_TICKER": str(rows[k].get("TICKER", "") or ""),
             "ISSUER_NAME": str(rows[k].get("ISSUER_NAME", "") or ""),
             "ISIN": str(rows[k].get("ISIN", "") or ""),
             "ISSUER_CUSIP": str(rows[k].get("ISSUER_CUSIP", "") or ""),
             "FIGI_CANDIDATES": json.dumps(mapping_details[k], sort_keys=True),
             "MAPPING_ERROR": ""}
            for k, v in mapping.items()
        ])

    sd = cal.index[cal.index.date <= pd.Timestamp(start_date).date()]
    ed = cal.index[cal.index.date <= pd.Timestamp(end_date).date()]
    sdate = sd[-1] if len(sd) else None
    edate = ed[-1] if len(ed) else None
    out = []
    for key, ticker in mapping.items():
        value = None
        if ticker and sdate is not None and edate is not None:
            try:
                p = price_series.get(ticker, pd.Series(dtype=float))
                # Require actual observations on both required market dates.
                if sdate in p.index and edate in p.index:
                    value = float(p.loc[edate] / p.loc[sdate] - 1)
            except Exception:
                pass
        out.append({
            "SECURITY_KEY": key, "RETURN": value, "TICKER_RESOLVED": ticker,
            "MAPPING_SOURCE": mapping_source[key],
            "NPORT_TICKER": str(rows[key].get("TICKER", "") or ""),
            "ISSUER_NAME": str(rows[key].get("ISSUER_NAME", "") or ""),
            "ISIN": str(rows[key].get("ISIN", "") or ""),
            "ISSUER_CUSIP": str(rows[key].get("ISSUER_CUSIP", "") or ""),
            "START_PRICE_DATE": str(sdate.date()) if sdate is not None else "",
            "END_PRICE_DATE": str(edate.date()) if edate is not None else "",
            "FIGI_CANDIDATES": json.dumps(mapping_details[key], sort_keys=True),
            "MAPPING_ERROR": ""
        })
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
