#!/usr/bin/env python3
"""Extract SEC Form N-SAR Item 69 index-fund answers by contemporaneous series.

A YES is a positive N-SAR index-fund answer. A NO means only that the filer
answered that the series was not an index fund; it is NOT an active label.
All matches require the filing's series header, Item 007 ordinal/name, and
Item 69 series coordinate to resolve consistently.
"""
import argparse, json, os, re, time
from pathlib import Path
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DELAY, MAX_BYTES = 0.12, 8 * 1024 * 1024
DEADLINE = None


def parse_sec_dates(values):
    """Parse SEC dates that may mix MM/DD/YYYY and ISO YYYY-MM-DD."""
    return pd.to_datetime(values, format="mixed", errors="coerce")


def make_session():
    email = os.environ.get("SEC_CONTACT_EMAIL", "").strip()
    if not email:
        raise RuntimeError("SEC_CONTACT_EMAIL secret is required")
    s = requests.Session()
    retry = Retry(total=2, connect=2, read=2, status=2, backoff_factor=.5,
                  status_forcelist=[408,429,500,502,503,504],
                  allowed_methods=frozenset(["GET"]), respect_retry_after_header=False,
                  raise_on_status=False)
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent":"The Rational Coward Research Project (tyoungg/market-structure-lab; contact "+email+")",
                      "Accept-Encoding":"gzip, deflate","Connection":"keep-alive"})
    return s


def get_text(s, url):
    global DEADLINE
    if DEADLINE is not None and time.monotonic() >= DEADLINE:
        raise TimeoutError("N-SAR Item 69 audit reached script deadline")
    if not url.startswith("https://www.sec.gov/Archives/edgar/data/"):
        raise ValueError("Refusing non-SEC submission URL")
    time.sleep(DELAY)
    r=s.get(url,timeout=(10,30),stream=True)
    r.raise_for_status()
    parts=[]; size=0
    try:
        for chunk in r.iter_content(65536):
            if not chunk: continue
            n=min(len(chunk),MAX_BYTES-size); parts.append(chunk[:n]); size+=n
            if size>=MAX_BYTES: break
    finally:
        r.close()
    if DEADLINE is not None and time.monotonic() >= DEADLINE:
        raise TimeoutError("N-SAR Item 69 audit reached script deadline")
    return b"".join(parts).decode("utf-8",errors="replace"), size>=MAX_BYTES


def norm_name(x):
    x=str(x or "").upper().replace("&"," AND ")
    return " ".join(re.findall(r"[A-Z0-9]+",x))


def parse_series_header(text):
    m=re.search(r"(?is)<SEC-HEADER>(.*?)</SEC-HEADER>",text)
    if not m: return {}
    h=m.group(1); out={}
    for sm in re.finditer(r"(?is)<SERIES>(.*?)(?=</SERIES>|<SERIES>)",h):
        b=sm.group(1)
        sid=re.search(r"(?is)<SERIES-ID>\s*(S\d{9})",b)
        name=re.search(r"(?is)<SERIES-NAME>\s*(.*?)\s*(?=<|$)",b)
        if sid and name:
            out[sid.group(1)]=re.sub(r"\s+"," ",name.group(1)).strip()
    return out


def extract_answer_body(text):
    for block in re.split(r"(?i)<DOCUMENT>",text)[1:]:
        head=re.split(r"(?i)<TEXT>",block,maxsplit=1)[0][:10000]
        typ=re.search(r"(?im)^\s*<TYPE>\s*([^\r\n<]+)",head)
        fname=re.search(r"(?im)^\s*<FILENAME>\s*([^\r\n<]+)",head)
        if not typ or typ.group(1).strip().upper() not in {"NSAR-A","NSAR-B","NSAR-AT","NSAR-BT"}:
            continue
        body=re.split(r"(?i)<TEXT>",block,maxsplit=1)
        if len(body)<2: continue
        return re.split(r"(?i)</TEXT>",body[1],maxsplit=1)[0], (fname.group(1).strip() if fname else "")
    return "", ""


def parse_item7_item69(body):
    series_names={}
    flags=[]
    period=re.search(r"(?im)^\s*000\s+[AB]000000\s+(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})\s*$",body)
    report_date=period.group(1) if period else ""
    for line in body.splitlines():
        m=re.match(r"^\s*007\s+C02(\d{2})00\s+(.+?)\s*$",line)
        if m:
            series_names[m.group(1)]=m.group(2).strip()
        m=re.match(r"^\s*069\s+([0-9A-Z]{6})\s+([YN])\s*$",line)
        if m:
            coord,value=m.group(1),m.group(2)
            ordinal=coord[2:4]
            scope="series" if ordinal.isdigit() and ordinal!="00" else (
                "all_series" if ordinal=="AA" else "registrant")
            flags.append({"coordinate":coord,"series_ordinal":ordinal,"value":value,"scope":scope})
    return series_names,flags,report_date


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--headers-csv",required=True,type=Path)
    ap.add_argument("--fund-year-csv",required=True,type=Path)
    ap.add_argument("--series-csv",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--max-runtime-minutes",type=int,default=25)
    a=ap.parse_args()
    global DEADLINE
    started=time.monotonic(); DEADLINE=started+a.max_runtime_minutes*60
    a.out.mkdir(parents=True,exist_ok=True)
    filings=pd.read_csv(a.headers_csv,dtype=str,keep_default_na=False)
    fy=pd.read_csv(a.fund_year_csv,dtype=str,keep_default_na=False)
    series=pd.read_csv(a.series_csv,dtype=str,keep_default_na=False)
    req_h={"cik","accession","form","filing_date","report_date","target_series_matches","submission_url","status"}
    req_fy={"fundno_key","year","matched_cik","matched_series_id","series_match_status"}
    req_s={"cik","series_id","series_name"}
    if not req_h.issubset(filings.columns) or not req_fy.issubset(fy.columns) or not req_s.issubset(series.columns):
        raise ValueError("Prior artifact schema mismatch")
    target_ciks=set(series.cik.astype(str).str.zfill(10))
    target_series=series[series.cik.astype(str).str.zfill(10).isin(target_ciks)].copy()
    if not target_ciks or target_series.empty:
        raise ValueError("Sample-only N-SAR series coverage file is empty")
    if target_series.series_id.duplicated().any():
        raise ValueError("Duplicate series IDs in sample-only N-SAR series coverage file")
    target_pairs=set(zip(target_series.cik.astype(str).str.zfill(10),target_series.series_id.astype(str)))
    filed_dates=pd.to_datetime(filings.filing_date,errors="coerce")
    chosen=filings[(filings.status.eq("target_series_id_found")) &
                   pd.to_numeric(filings.target_series_matches,errors="coerce").gt(0) &
                   filed_dates.le(pd.Timestamp("2009-12-31"))].copy()
    sess=make_session()
    evidence=[]; registrant=[]; unmatched=[]; errors=[]; completed=0; timed_out=False
    for i,row in enumerate(chosen.to_dict("records"),1):
        if time.monotonic()>=DEADLINE:
            timed_out=True; break
        cik=str(row["cik"]).zfill(10); url=str(row["submission_url"])
        try:
            text,truncated=get_text(sess,url)
            header_series=parse_series_header(text)
            body,filename=extract_answer_body(text)
            if not body:
                unmatched.append({"cik":cik,"accession":row["accession"],"reason":"NSAR_answer_document_not_found"})
                completed+=1; continue
            item7,flags,body_report_date=parse_item7_item69(body)
            report_date=body_report_date or row["report_date"]
            name_to_ids={}
            for sid,nm in header_series.items():
                name_to_ids.setdefault(norm_name(nm),[]).append(sid)
            ordinal_to_sid={}
            for ordinal,nm in item7.items():
                ids=name_to_ids.get(norm_name(nm),[])
                if len(ids)==1:
                    ordinal_to_sid[ordinal]=ids[0]
                elif len(ids)>1:
                    unmatched.append({"cik":cik,"accession":row["accession"],"series_ordinal":ordinal,
                                      "item7_series_name":nm,"reason":"duplicate_header_series_name"})
            per_series={}
            for flag in flags:
                if flag["scope"]=="registrant":
                    registrant.append({"cik":cik,"accession":row["accession"],"filing_date":row["filing_date"],
                                       "report_date":report_date,"form":row["form"],
                                       "index_fund_flag":flag["value"],"scope":"registrant"})
                    continue
                ords=list(item7) if flag["scope"]=="all_series" else [flag["series_ordinal"]]
                for ordinal in ords:
                    sid=ordinal_to_sid.get(ordinal)
                    if not sid:
                        unmatched.append({"cik":cik,"accession":row["accession"],"series_ordinal":ordinal,
                                          "item7_series_name":item7.get(ordinal,""),
                                          "reason":"item7_name_not_uniquely_matched_to_header_series"})
                        continue
                    if (cik,sid) not in target_pairs:
                        continue
                    per_series.setdefault(sid,[]).append(flag["value"])
            for sid,values in per_series.items():
                t=target_series[(target_series.cik.astype(str).str.zfill(10).eq(cik)) &
                                target_series.series_id.astype(str).eq(sid)].iloc[0]
                uniq=sorted(set(values))
                evidence.append({"cik":cik,"series_id":sid,"registry_series_name":t.series_name,
                                 "historical_header_series_name":header_series.get(sid,""),
                                 "item7_series_name":next((item7[o] for o,x in ordinal_to_sid.items() if x==sid),""),
                                 "index_fund_flag":uniq[0] if len(uniq)==1 else "CONFLICT",
                                 "duplicate_item69_values":"|".join(values),
                                 "filing_date":row["filing_date"],"report_date":report_date,
                                 "form":row["form"],"accession":row["accession"],"submission_url":url,
                                 "answer_filename":filename,"truncated_submission_prefix":truncated})
            completed+=1
        except Exception as e:
            errors.append({"cik":cik,"accession":row["accession"],"error":f"{type(e).__name__}:{e}"})
        if i%20==0:
            pd.DataFrame(evidence).to_csv(a.out/"nsar_item69_series_evidence_checkpoint.csv",index=False)
            print(f"Processed {i}/{len(chosen)} selected filings; evidence rows={len(evidence)}",flush=True)
    ev=pd.DataFrame(evidence)
    if ev.empty:
        ev=pd.DataFrame(columns=["cik","series_id","registry_series_name","historical_header_series_name",
                                 "item7_series_name","index_fund_flag","duplicate_item69_values",
                                 "filing_date","report_date","form","accession","submission_url",
                                 "answer_filename","truncated_submission_prefix"])
    ev.to_csv(a.out/"nsar_item69_series_evidence.csv",index=False)
    pd.DataFrame(registrant).to_csv(a.out/"nsar_item69_registrant_level.csv",index=False)
    pd.DataFrame(unmatched).to_csv(a.out/"nsar_item69_unmatched.csv",index=False)
    pd.DataFrame(errors).to_csv(a.out/"nsar_item69_errors.csv",index=False)

    ev["filing_date_dt"]=parse_sec_dates(ev.filing_date)
    ev["report_date_dt"]=parse_sec_dates(ev.report_date)
    fy=fy.copy()
    fy["year_num"]=pd.to_numeric(fy.year,errors="coerce")
    fy["matched_cik_norm"]=fy.matched_cik.astype(str).str.zfill(10)
    asof=[]
    for r in fy.to_dict("records"):
        year=r.get("year_num"); cik=r.get("matched_cik_norm"); sid=str(r.get("matched_series_id") or "")
        if not cik or cik=="NAN":
            asof.append({**r,"nsar_index_fund_status":"unclassified_no_CIK"}); continue
        if cik not in target_ciks:
            asof.append({**r,"nsar_index_fund_status":"unclassified_CIK_not_in_N-SAR_sample"}); continue
        if pd.isna(year) or r.get("series_match_status")!="unique_series" or not sid or sid=="nan":
            asof.append({**r,"nsar_index_fund_status":"unclassified_no_unique_SEC_series"}); continue
        cutoff=pd.Timestamp(year=int(year),month=1,day=1)
        prior=ev[(ev.cik.astype(str).str.zfill(10).eq(cik)) & ev.series_id.eq(sid) &
                 (ev.filing_date_dt<cutoff) & (ev.report_date_dt<cutoff) &
                 (ev.report_date_dt>=cutoff-pd.Timedelta(days=548))].copy()
        if prior.empty:
            asof.append({**r,"nsar_index_fund_status":"unclassified_no_recent_prior_N-SAR"}); continue
        latest=prior.filing_date_dt.max()
        last=prior[prior.filing_date_dt.eq(latest)]
        labels=set(last.index_fund_flag.astype(str))
        label=next(iter(labels)) if len(labels)==1 else "CONFLICT"
        status={"Y":"n_sar_index_fund_yes","N":"n_sar_index_fund_no_not_active",
                "CONFLICT":"unclassified_conflicting_item69"}.get(label,"unclassified_item69_value")
        asof.append({**r,"nsar_index_fund_status":status,
                     "nsar_index_fund_flag":label,"nsar_filing_date":str(latest.date()),
                     "nsar_report_date":str(last.report_date.iloc[0]),
                     "nsar_accession":"|".join(last.accession.astype(str).unique())})
    asof=pd.DataFrame(asof)
    asof.to_csv(a.out/"nsar_item69_fund_year_asof.csv",index=False)
    annual=(asof.groupby("year").nsar_index_fund_status.value_counts().unstack(fill_value=0)
            .reset_index())
    annual.to_csv(a.out/"nsar_item69_annual_coverage.csv",index=False)
    flags=ev.index_fund_flag.value_counts().to_dict()
    metrics={
      "source":"SEC Form N-SAR Item 69, contemporaneous answer.fil",
      "sample_ciks":int(len(target_ciks)),"sampled_target_series":int(len(target_series)),
      "selected_header_filings_with_target_series_through_2009":int(len(chosen)),
      "fund_year_rows_in_sample":int(asof.matched_cik.astype(str).str.zfill(10).isin(target_ciks).sum()),
      "answer_documents_processed":completed,
      "item69_series_evidence_rows":int(len(ev)),
      "target_series_with_item69_evidence":int(ev.series_id.nunique()) if not ev.empty else 0,
      "target_series_item69_yes":int(ev.loc[ev.index_fund_flag.eq("Y"),"series_id"].nunique()) if not ev.empty else 0,
      "target_series_item69_no":int(ev.loc[ev.index_fund_flag.eq("N"),"series_id"].nunique()) if not ev.empty else 0,
      "item69_flag_counts":flags,
      "registrant_level_item69_rows":len(registrant),
      "unmatched_item69_rows":len(unmatched),"errors":len(errors),
      "fund_year_rows":len(asof),
      "fund_year_n_sar_yes":int(asof.nsar_index_fund_status.eq("n_sar_index_fund_yes").sum()),
      "fund_year_n_sar_no_not_active":int(asof.nsar_index_fund_status.eq("n_sar_index_fund_no_not_active").sum()),
      "fund_year_unclassified":int(asof.nsar_index_fund_status.str.startswith("unclassified").sum()),
      "runtime_minutes":round((time.monotonic()-started)/60,2),
      "runtime_deadline_minutes":a.max_runtime_minutes,
      "runtime_deadline_reached":bool(timed_out or time.monotonic()>=DEADLINE),
      "asof_rule":"Use only filings filed before January 1 of the fund-year, with report date also before that cutoff and no more than 548 days old.",
      "interpretation":"Item 69 YES is a direct positive index-fund answer. Item 69 NO is not an active label; it may include enhanced-index or active funds. No active-only classification is created."
    }
    (a.out/"nsar_item69_metrics.json").write_text(json.dumps(metrics,indent=2,default=str)+"\n")
    report=["# N-SAR Item 69 Index-Fund Flag Audit","",
      "**Classification boundary:** Item 69 YES is positive evidence that the registrant/series reported itself as an index fund. Item 69 NO is not evidence of active management and is retained as a separate non-index response. No active-only universe is created.","",
      "## Metrics","",json.dumps(metrics,indent=2,default=str),"",
      "## Method","",
      "The script reads the N-SAR answer document from each sampled submission, parses Item 007's series ordinal/name list and Item 69's Y/N response, and maps the ordinal to the SEC series ID only through a unique normalized name match between Item 007 and the same filing's SEC header. Ambiguous and unmatched names are retained as unresolved; no positional guess is used.",
      "Fund-year as-of labels require the N-SAR filing date to precede January 1 of the observation year and the reported period to be no more than 548 days old. Same-year filings are not backdated.",
      "The sample denominator is taken from the sample-only series-coverage input, not inferred from CIKs that happened to return filings. Only filings dated on or before 2009-12-31 are downloaded for this 1979-2009 panel. Fund-year rows belonging to the other 471 registrants are explicitly marked unclassified_CIK_not_in_N-SAR_sample. The sample is deterministic, not probability-representative; do not extrapolate.","",
      "## Outputs","",
      "- nsar_item69_series_evidence.csv — direct per-series Item 69 answers.",
      "- nsar_item69_fund_year_asof.csv — conservative as-of labels joined to fund-year records.",
      "- nsar_item69_annual_coverage.csv — annual fund-year coverage.",
      "- nsar_item69_registrant_level.csv — responses not safely assignable to a single series.",
      "- nsar_item69_unmatched.csv — unresolved ordinal/name mappings.",
      "- nsar_item69_errors.csv — bounded retrieval errors.",
      "- nsar_item69_metrics.json — machine-readable audit totals.",""]
    (a.out/"NSAR_ITEM69_INDEX_FLAG_AUDIT.md").write_text("\n".join(report),encoding="utf-8")
    print(json.dumps(metrics,indent=2,default=str))


if __name__=="__main__":
    main()
