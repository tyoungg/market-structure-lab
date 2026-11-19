#!/usr/bin/env python3
"""Reproducible public Petajisto-to-SEC series/class and filing-evidence audit."""
import argparse, difflib, hashlib, json, os, re, time
from pathlib import Path
import pandas as pd
import requests

SEC_UA = "The Rational Coward Research Project (tyoungg/market-structure-lab; contact " + os.environ.get("SEC_CONTACT_EMAIL", "") + ")"
FORMS = {"485APOS","485BPOS","485BXT","N-1A","497","497K","497J","N-CSR","N-CSRS"}
PRIORITY = {"485BPOS":0,"485APOS":1,"497K":2,"497":3,"N-1A":4,"497J":5,"N-CSR":6,"N-CSRS":7,"485BXT":8}

def clean(s):
    return s.astype("string").str.strip().replace({"":"", "nan":pd.NA, "None":pd.NA}).replace("",pd.NA).str.replace(r"\.0$","",regex=True)

def period_ym(s):
    x=s.astype("string").str.strip().str.replace(r"\.0$","",regex=True)
    z=x.str.extract(r"^(\d{4})[mM]?(\d{1,2})$")
    m=pd.to_numeric(z[1],errors="coerce")
    d=pd.to_datetime(z[0]+m.astype("Int64").astype("string").str.zfill(2),format="%Y%m",errors="coerce")
    return d.dt.to_period("M").astype("string")

def norm(s):
    if pd.isna(s): return ""
    x=str(s).upper().replace("&"," AND ")
    # Preserve meaningful fund-name terms such as SELECT; remove generic legal/class words only.
    x=re.sub(r"\b(CLASS|SHARES?|FUND|FUNDS|PORTFOLIO|SERIES)\b"," ",x)
    return " ".join(re.findall(r"[A-Z0-9]+",x))

def pet_name_norm(s):
    if pd.isna(s): return ""
    x=str(s).strip()
    if ":" in x: x=x.rsplit(":",1)[-1]
    if ";" in x: x=x.split(";",1)[0]
    return norm(x)

def ticker_norm(s):
    if pd.isna(s): return ""
    return re.sub(r"[^A-Z0-9]","",str(s).upper().strip())

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def pick_col(cols, tests):
    normed={re.sub(r"[^a-z0-9]","",c.lower()):c for c in cols}
    for test in tests:
        if test in normed: return normed[test]
    for key,original in normed.items():
        if any(t in key for t in tests): return original
    return None

def load_sec(path):
    df=pd.read_csv(path,dtype="string",encoding_errors="replace",low_memory=False)
    cols=list(df.columns)
    aliases={
      "cik":["cik","centralindexkey"],"company":["nameofinvestmentcompany","companyname","registrantname"],
      "series_id":["seriesid"],"series_name":["seriesname"],"class_id":["classid","classcontractid"],
      "class_name":["classname","classcontractname"],"ticker":["classticker","ticker"],
      "file_number":["reportingfilenumber","filenumber"],"org_type":["organizationtype","formtype"]}
    mapped={k:pick_col(cols,v) for k,v in aliases.items()}
    required=["cik","series_id","series_name","class_id","class_name","ticker"]
    missing=[k for k in required if mapped[k] is None]
    if missing: raise ValueError(f"SEC columns not recognized: {missing}; headers={cols}")
    out=pd.DataFrame()
    for k,col in mapped.items(): out[k]=df[col].astype("string").str.strip() if col else ""
    out["cik"]=out.cik.str.replace(r"\D","",regex=True).str.zfill(10)
    out["ticker_key"]=out.ticker.map(ticker_norm)
    out["series_key"]=out.series_id.str.strip()
    out["class_key"]=out.class_id.str.strip()
    out["series_name_key"]=out.series_name.map(norm)
    out["class_name_key"]=out.class_name.map(norm)
    out["company_name_key"]=out.company.map(norm)
    return out.drop_duplicates(["cik","series_key","class_key","ticker_key"]),mapped

def load_eligible(tr_zip,pet_csv):
    import zipfile
    with zipfile.ZipFile(tr_zip) as z:
        csvs=[n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(csvs)!=1: raise ValueError(f"TR ZIP expected one CSV, found {csvs}")
        with z.open(csvs[0]) as f: tr=pd.read_csv(f,dtype={"fundno":"string","wficn":"string"},low_memory=False)
    repairs=[]
    def repair(fields):
        repairs.append(len(fields)>15)
        return fields[:14]+[",".join(fields[14:])] if len(fields)>15 else fields
    p=pd.read_csv(pet_csv,dtype="string",engine="python",on_bad_lines=repair)
    p.columns=[str(c).strip().lower() for c in p.columns]
    if not {"fundno","wficn","rdate","ticker","fund_name"}.issubset(p.columns):
        raise ValueError(f"Unexpected Petajisto fields: {list(p.columns)}")
    tr["fundno_key"]=clean(tr.fundno); tr["wficn_key"]=clean(tr.wficn); tr["period"]=period_ym(tr.ym)
    p["fundno_key"]=clean(p.fundno); p["wficn_key"]=clean(p.wficn)
    p["period"]=pd.to_datetime(p.rdate,errors="coerce").dt.to_period("M").astype("string")
    if tr.period.isna().any() or p.period.isna().all(): raise ValueError("Date parsing failed")
    pf=p.dropna(subset=["fundno_key","period"]).copy()
    conflicts=pf.groupby(["fundno_key","period"]).wficn_key.nunique(dropna=True).gt(1)
    conflict_keys=set(conflicts[conflicts].index.tolist())
    pf=pf.sort_values(["fundno_key","period"]).drop_duplicates(["fundno_key","period"])
    t=tr.sort_values(["fundno_key","period"]).drop_duplicates(["fundno_key","period"])
    m=pf.merge(t[["fundno_key","period","wficn_key"]],on=["fundno_key","period"],how="inner",suffixes=("_pet","_tr"))
    keys=list(zip(m.fundno_key,m.period)); m["ambiguous_key"]=[k in conflict_keys for k in keys]
    m=m.loc[~m.ambiguous_key].copy()
    agree=m.wficn_key_pet.notna() & m.wficn_key_tr.notna() & m.wficn_key_pet.eq(m.wficn_key_tr)
    recover=m.wficn_key_tr.isna() & m.wficn_key_pet.notna()
    m["link_type"]="excluded"
    m.loc[agree,"link_type"]="primary_wficn_agreement"
    m.loc[recover,"link_type"]="recovered_missing_tr_wficn"
    m=m.loc[m.link_type.ne("excluded")].copy()
    m["year"]=m.period.str[:4]
    m["ticker_key"]=m.ticker.map(ticker_norm)
    m["pet_name_key"]=m.fund_name.map(pet_name_norm)
    return m,p,tr,len(repairs),sum(repairs),len(conflict_keys)

def match_registry(eligible,sec):
    identity=(eligible.groupby(["fundno_key","period","year"],dropna=False)
      .agg(ticker=("ticker",lambda x:next((v for v in x if pd.notna(v) and str(v).strip()),"")),
           fund_name=("fund_name",lambda x:next((v for v in x if pd.notna(v) and str(v).strip()),"")),
           period_keys=("period","nunique"),
           link_type=("link_type",lambda x:"recovered_missing_tr_wficn" if (x=="recovered_missing_tr_wficn").any() else "primary_wficn_agreement"))
      .reset_index())
    identity["ticker_key"]=identity.ticker.map(ticker_norm); identity["name_key"]=identity.fund_name.map(norm)
    ticker_map={k:g.index.tolist() for k,g in sec.groupby("ticker_key") if k}
    token_map={}
    sec_records=sec.to_dict("records")
    for j,s in enumerate(sec_records):
        tokens=set()
        for v in [s["series_name_key"],s["class_name_key"]]:
            tokens.update(re.findall(r"[A-Z0-9]{3,}",v or ""))
        for tok in tokens: token_map.setdefault(tok,set()).add(j)
    rows=[]
    for r in identity.to_dict("records"):
        cand=set(ticker_map.get(r["ticker_key"],[])) if r["ticker_key"] else set()
        qt=set(re.findall(r"[A-Z0-9]{3,}",r["name_key"]))
        if qt:
            counts={}
            for tok in qt:
                for j in token_map.get(tok,()): counts[j]=counts.get(j,0)+1
            cand.update(j for j,n in counts.items() if n>=2 or len(qt)==1 and n==1)
        for j in cand:
            s=sec_records[j]
            vals=[s["series_name_key"],s["class_name_key"]]
            score=max((difflib.SequenceMatcher(None,r["name_key"],v).ratio() for v in vals if r["name_key"] and v),default=0)
            tm=bool(r["ticker_key"] and r["ticker_key"]==s["ticker_key"])
            if tm or score>=0.72:
                rows.append({**r,"cik":s["cik"],"series_id":s["series_key"],"series_name":s["series_name"],
                  "class_id":s["class_key"],"class_name":s["class_name"],"sec_ticker":s["ticker"],
                  "sec_company":s["company"],"ticker_match":tm,"name_similarity":round(score,4),
                  "match_rule":"ticker+name candidate" if tm else "name-similarity candidate"})
    cand_df=pd.DataFrame(rows)
    if cand_df.empty:
        identity["series_match_status"]="no_strict_candidate"
        identity["strict_series_count"]=0; identity["strict_class_count"]=0; identity["share_class_ambiguous"]=False
        return identity,cand_df,cand_df
    cand_df["strict_candidate"]=(cand_df.ticker_match & (cand_df.name_similarity>=0.65)) | (cand_df.name_similarity>=0.90)
    strict=cand_df[cand_df.strict_candidate].copy()
    stats=[]
    for (fundno,period,year),g in strict.groupby(["fundno_key","period","year"]):
        series=sorted(g.series_id.dropna().unique().tolist())
        classes=sorted(g.class_id.dropna().unique().tolist())
        best=g.sort_values(["ticker_match","name_similarity"],ascending=False)
        stats.append({"fundno_key":fundno,"period":period,"year":year,"strict_series_count":len(series),"strict_class_count":len(classes),
          "matched_series_id":series[0] if len(series)==1 else "",
          "matched_cik":best.iloc[0].cik if len(series)==1 else "",
          "matched_series_name":best.iloc[0].series_name if len(series)==1 else "",
          "matched_class_id":classes[0] if len(classes)==1 else "",
          "top_name_similarity":float(best.name_similarity.max()),
          "series_match_status":"unique_series" if len(series)==1 else "multiple_series_ambiguous"})
    identity=identity.merge(pd.DataFrame(stats),on=["fundno_key","period","year"],how="left")
    identity["series_match_status"]=identity.series_match_status.fillna("no_strict_candidate")
    identity["strict_series_count"]=identity.strict_series_count.fillna(0).astype(int)
    identity["strict_class_count"]=identity.strict_class_count.fillna(0).astype(int)
    identity["share_class_ambiguous"]=identity.strict_series_count.eq(1)&identity.strict_class_count.gt(1)
    return identity,cand_df,strict

def diagnostics(sec,eligible):
    tick=sec[sec.ticker_key.ne("")].groupby("ticker_key").agg(sec_class_records=("class_key","nunique"),
      sec_series=("series_key","nunique"),sec_ciks=("cik","nunique"),
      example_names=("series_name",lambda x:" | ".join(list(x.dropna().unique())[:3]))).reset_index()
    tick["ticker_collision"]=(tick.sec_series>1)|(tick.sec_ciks>1)
    pet=eligible[eligible.ticker_key.ne("")].groupby("ticker_key").agg(petajisto_funds=("fundno_key","nunique"),
      petajisto_periods=("period","nunique")).reset_index()
    tick=tick.merge(pet,on="ticker_key",how="left")
    tick["petajisto_funds"]=tick.petajisto_funds.fillna(0).astype(int)
    pn=eligible[eligible.pet_name_key.ne("")].groupby("pet_name_key").agg(petajisto_funds=("fundno_key","nunique"),
      example_name=("fund_name","first")).reset_index()
    pn=pn[pn.petajisto_funds.gt(1)].sort_values("petajisto_funds",ascending=False)
    sn=sec[sec.series_name_key.ne("")].groupby("series_name_key").agg(sec_series=("series_key","nunique"),
      sec_ciks=("cik","nunique"),example_name=("series_name","first")).reset_index()
    sn=sn[(sn.sec_series>1)|(sn.sec_ciks>1)]
    pet_ticker_year=(eligible[eligible.ticker_key.ne("")].groupby(["year","ticker_key"])
      .agg(petajisto_funds=("fundno_key","nunique"),period_records=("period","size"),
           example_name=("fund_name","first")).reset_index())
    pet_ticker_year=pet_ticker_year[pet_ticker_year.petajisto_funds.gt(1)].sort_values(
      ["year","petajisto_funds","ticker_key"])
    return tick,pn,sn,pet_ticker_year

def session():
    if not os.environ.get("SEC_CONTACT_EMAIL"):
        raise RuntimeError("SEC_CONTACT_EMAIL environment variable is required for the SEC User-Agent")
    s=requests.Session()
    s.headers.update({"User-Agent":SEC_UA,"Accept-Encoding":"gzip, deflate"})
    return s

def get_json(s,url):
    r=s.get(url,timeout=45); r.raise_for_status(); return r.json()

def get_filing(s,cik,accession):
    acc=accession.replace("-","")
    url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{accession}.txt"
    r=s.get(url,timeout=60); r.raise_for_status()
    return url,r.text

def docs_from_sgml(full):
    docs=[]
    for block in re.findall(r"<DOCUMENT>(.*?)</DOCUMENT>",full,flags=re.I|re.S):
        typ=re.search(r"<TYPE>\s*([^\r\n<]+)",block,flags=re.I)
        fn=re.search(r"<FILENAME>\s*([^\r\n<]+)",block,flags=re.I)
        body=re.search(r"<TEXT>(.*?)</TEXT>",block,flags=re.I|re.S)
        if not body: continue
        raw=re.sub(r"(?is)<script.*?</script>|<style.*?</style>"," ",body.group(1))
        txt=re.sub(r"(?s)<[^>]+>"," ",raw)
        txt=re.sub(r"&nbsp;|&#160;"," ",txt,flags=re.I)
        txt=re.sub(r"&amp;","&",txt,flags=re.I)
        txt=re.sub(r"\s+"," ",txt)
        docs.append({"form":typ.group(1).strip() if typ else "","filename":fn.group(1).strip() if fn else "","text":txt})
    return docs

def series_context(text, series_name, radius=1500):
    # Use only text immediately following the first exact series-name occurrence.
    # This intentionally sacrifices recall to avoid borrowing strategy language
    # from another fund elsewhere in a registrant's combined filing.
    if not series_name or len(norm(series_name).replace(" ","")) < 8:
        return []
    m=re.search(re.escape(str(series_name)),text,flags=re.I)
    if not m:
        return []
    a=m.end()
    return [text[a:min(len(text),a+radius)]]

def classify(text):
    t=re.sub(r"\s+"," ",text.lower())
    pats={
      "enhanced index":[r"enhanced[\s-]+index(?:ing)?",r"index[\s-]+enhancement"],
      "index":[r"\bis an index fund\b",r"\bpassively managed\b",
               r"\bseeks? to track (?:the )?(?:investment results|performance)",
               r"\bfull replication strategy\b",r"replicate the performance of",
               r"correspond generally to the performance of"],
      "active":[r"\bis actively managed\b",r"\bactively manages\b",
               r"\bactive stock selection\b",r"\bactive management strategy\b",
               r"does not seek to track",r"is not an index fund"]}
    found={k:[m.group(0) for p in ps for m in re.finditer(p,t)] for k,ps in pats.items()}
    present=[k for k,v in found.items() if v]
    if "enhanced index" in present: label="enhanced index"
    elif "index" in present and "active" not in present: label="index"
    elif "active" in present and "index" not in present: label="active"
    else: label="unclassified"
    return label,found

def fetch_evidence(identity,out,max_per_year):
    targets=identity[identity.series_match_status.eq("unique_series")].copy()
    if targets.empty: return pd.DataFrame()
    lookup=targets.groupby(["matched_cik","matched_series_id","matched_series_name"]).agg(
      fundnos=("fundno_key",lambda x:"|".join(sorted(set(x)))),
      first_year=("year","min"),last_year=("year","max")).reset_index()
    s=session(); output=[]
    for cik in sorted(lookup.matched_cik.astype(str).unique()):
        try:
            sub=get_json(s,f"https://data.sec.gov/submissions/CIK{str(cik).zfill(10)}.json")
            df=pd.DataFrame(sub.get("filings",{}).get("recent",{}))
            if df.empty: continue
            df["filingDate"]=pd.to_datetime(df.get("filingDate"),errors="coerce")
            df["form"]=df.get("form","").astype(str)
            df=df[df.form.isin(FORMS)&df.filingDate.dt.year.between(1994,2009)].copy()
            if df.empty: continue
            df["priority"]=df.form.map(PRIORITY).fillna(99)
            selected=[]
            for yr,g in df.groupby(df.filingDate.dt.year):
                selected.extend(g.sort_values(["priority","filingDate"],ascending=[True,False]).head(max_per_year).to_dict("records"))
            for f in selected:
                acc=str(f.get("accessionNumber",""))
                if not acc: continue
                try:
                    url,full=get_filing(s,cik,acc)
                    ids=set(re.findall(r"\bS\d{9}\b",full))
                    docs=docs_from_sgml(full)
                    for sr in lookup[lookup.matched_cik.astype(str).eq(str(cik))].to_dict("records"):
                        sid=str(sr["matched_series_id"])
                        if sid not in ids: continue
                        chunks=[]
                        for d in docs:
                            if any(k in (d["form"]+" "+d["filename"]).lower() for k in ["497","485","n-1a"]):
                                chunks.extend(series_context(d["text"],sr["matched_series_name"]))
                        if not chunks: continue
                        evidence_text=" ".join(chunks)
                        label,found=classify(evidence_text)
                        phrases=[f"{k}:{v}" for k,vs in found.items() for v in vs[:3]]
                        output.append({"cik":str(cik).zfill(10),"series_id":sid,"series_name":sr["matched_series_name"],
                          "filing_date":str(f["filingDate"].date()),"form":f.get("form"),"accession":acc,
                          "filing_url":url,"document_count":len(chunks),"classification":label,
                          "evidence_phrases":" | ".join(phrases),"evidence_context":evidence_text[:1500],
                          "fundnos":sr["fundnos"],"series_ids_in_filing":len(ids)})
                except Exception as e:
                    output.append({"cik":str(cik).zfill(10),"series_id":"","series_name":"",
                      "filing_date":str(f.get("filingDate","")),"form":f.get("form"),"accession":acc,
                      "filing_url":"","document_count":0,"classification":"unclassified",
                      "evidence_phrases":f"DOWNLOAD_ERROR:{type(e).__name__}:{e}","fundnos":"","series_ids_in_filing":0})
                time.sleep(0.15)
        except Exception as e:
            output.append({"cik":str(cik).zfill(10),"series_id":"","series_name":"","filing_date":"",
              "form":"SUBMISSIONS_API","accession":"","filing_url":"","document_count":0,
              "classification":"unclassified","evidence_phrases":f"API_ERROR:{type(e).__name__}:{e}",
              "fundnos":"","series_ids_in_filing":0})
        time.sleep(0.15)
    ev=pd.DataFrame(output)
    if not ev.empty: ev.to_csv(out/"sec_filing_evidence.csv",index=False)
    return ev

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tr-zip",required=True,type=Path); ap.add_argument("--petajisto",required=True,type=Path)
    ap.add_argument("--sec-series-class",required=True,type=Path); ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--skip-filings",action="store_true"); ap.add_argument("--max-filings-per-cik-year",type=int,default=2)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    eligible,p,tr,repair_rows,repair_count,conflict_count=load_eligible(a.tr_zip,a.petajisto)
    primary=int(eligible.link_type.eq("primary_wficn_agreement").sum())
    recovered=int(eligible.link_type.eq("recovered_missing_tr_wficn").sum())
    if (primary,recovered)!=(63428,409):
        raise ValueError(f"Eligible source population changed: primary={primary}, recovered={recovered}")
    sec,sec_cols=load_sec(a.sec_series_class)
    identity,cands,strict=match_registry(eligible,sec)
    tick,pn,sn,pet_ticker_year=diagnostics(sec,eligible)
    identity.to_csv(a.out/"sec_match_by_fund_period.csv",index=False)
    cands.to_csv(a.out/"sec_match_candidates.csv",index=False)
    tick.to_csv(a.out/"sec_ticker_collision_audit.csv",index=False)
    pet_ticker_year.to_csv(a.out/"petajisto_ticker_year_collision_audit.csv",index=False)
    pn.to_csv(a.out/"petajisto_name_collision_audit.csv",index=False)
    sn.to_csv(a.out/"sec_series_name_collision_audit.csv",index=False)
    annual=identity.groupby("year").agg(
      eligible_fund_periods=("fundno_key","size"),unique_petajisto_funds=("fundno_key","nunique"),
      unique_series_matches=("series_match_status",lambda x:int((x=="unique_series").sum())),
      multiple_series_ambiguous=("series_match_status",lambda x:int((x=="multiple_series_ambiguous").sum())),
      no_strict_candidate=("series_match_status",lambda x:int((x=="no_strict_candidate").sum())),
      share_class_ambiguous=("share_class_ambiguous","sum"),
      recovery_fund_periods=("link_type",lambda x:int((x=="recovered_missing_tr_wficn").sum()))).reset_index()
    annual["unique_series_match_pct"]=(100*annual.unique_series_matches/annual.eligible_fund_periods).round(2)
    annual.to_csv(a.out/"sec_match_rates_by_year.csv",index=False)
    fy=[]
    for (fundno,year),g in identity.groupby(["fundno_key","year"]):
        matched=sorted(g.loc[g.series_match_status.eq("unique_series"),"matched_series_id"].dropna().astype(str).unique())
        ambiguous=bool(g.series_match_status.eq("multiple_series_ambiguous").any()) or len(matched)>1
        status="multiple_series_ambiguous" if ambiguous else ("unique_series" if len(matched)==1 else "no_strict_candidate")
        fy.append({"fundno_key":fundno,"year":year,"period_records":len(g),
          "unique_series_periods":int(g.series_match_status.eq("unique_series").sum()),
          "ambiguous_periods":int(g.series_match_status.eq("multiple_series_ambiguous").sum()),
          "no_candidate_periods":int(g.series_match_status.eq("no_strict_candidate").sum()),
          "series_match_status":status,"matched_series_id":matched[0] if len(matched)==1 and not ambiguous else "",
          "share_class_ambiguous":bool(g.share_class_ambiguous.any()),
          "link_type":"recovered_missing_tr_wficn" if g.link_type.eq("recovered_missing_tr_wficn").any() else "primary_wficn_agreement"})
    fund_year=pd.DataFrame(fy)
    fund_year.to_csv(a.out/"sec_match_by_fund_year.csv",index=False)
    metrics={"petajisto_period_window":[str(eligible.period.min()),str(eligible.period.max())],
      "eligible_fund_period_records":len(eligible),"primary_wficn_agreement_records":primary,
      "separately_flagged_recoveries":recovered,"excluded_conflict_keys":conflict_count,
      "sec_registry_snapshot":"2010","sec_registry_class_rows":len(sec),"sec_registry_unique_series":int(sec.series_key.nunique()),
      "sec_registry_unique_classes":int(sec.class_key.nunique()),"sec_registry_unique_ciks":int(sec.cik.nunique()),
      "fund_period_rows":len(identity),"unique_series_fund_periods":int((identity.series_match_status=="unique_series").sum()),
      "multiple_series_ambiguous_fund_periods":int((identity.series_match_status=="multiple_series_ambiguous").sum()),
      "no_strict_candidate_fund_periods":int((identity.series_match_status=="no_strict_candidate").sum()),
      "fund_year_rows":len(fund_year),
      "unique_series_fund_years":int((fund_year.series_match_status=="unique_series").sum()),
      "multiple_series_ambiguous_fund_years":int((fund_year.series_match_status=="multiple_series_ambiguous").sum()),
      "no_strict_candidate_fund_years":int((fund_year.series_match_status=="no_strict_candidate").sum()),
      "share_class_ambiguous_fund_years":int(fund_year.share_class_ambiguous.sum()),
      "sec_ticker_collision_count":int(tick.ticker_collision.sum()),
      "petajisto_ticker_year_collision_count":len(pet_ticker_year),
      "petajisto_name_collision_count":len(pn),"sec_series_name_collision_count":len(sn),
      "sec_columns":sec_cols,"petajisto_malformed_name_rows_repaired":int(repair_count),
      "sha256":{"sec_registry":sha256(a.sec_series_class),"petajisto":sha256(a.petajisto),"tr_zip":sha256(a.tr_zip)},
      "caveat":"2010 SEC registry snapshot matched to contemporaneous Petajisto names/tickers; not proof of historical SEC status. A unique series can have multiple classes."}
    ev=pd.DataFrame()
    if not a.skip_filings:
        ev=fetch_evidence(identity,a.out,a.max_filings_per_cik_year)
        if not ev.empty:
            good=ev[ev.series_id.ne("")]
            def conservative_label(x):
                labels=set(x)-{"unclassified"}
                return next(iter(labels)) if len(labels)==1 and "unclassified" not in set(x) else "unclassified"
            labels=good.groupby("series_id").classification.apply(conservative_label).rename("filing_evidence_class").reset_index()
            identity=identity.merge(labels,left_on="matched_series_id",right_on="series_id",how="left")
            identity["filing_evidence_class"]=identity.filing_evidence_class.fillna("unclassified")
            identity.to_csv(a.out/"sec_match_by_fund_period.csv",index=False)
            fund_year=fund_year.merge(labels,left_on="matched_series_id",right_on="series_id",how="left")
            fund_year["filing_evidence_class"]=fund_year.filing_evidence_class.fillna("unclassified")
            fund_year.to_csv(a.out/"sec_match_by_fund_year.csv",index=False)
            metrics["series_with_filing_evidence"]=int(good.series_id.nunique())
            metrics["filing_evidence_rows"]=len(good)
            metrics["filing_classification_counts"]=good.groupby("classification").size().to_dict()
    pd.Series(metrics).to_json(a.out/"sec_bridge_metrics.json",indent=2,force_ascii=False)
    report=["# Petajisto-to-SEC Series/Class Bridge Audit","",
      "Status: reproducible public-data linkage audit; SEC filing labels are conservative evidence classifications.","",
      "## Eligible Petajisto/TR population",f"- Primary agreeing-WFICN records: {primary:,}",
      f"- Separately flagged missing-TR-WFICN recoveries: {recovered:,}",f"- Excluded WFICN conflict keys: {conflict_count:,}",
      f"- SEC 2010 registry: {len(sec):,} classes, {sec.series_key.nunique():,} series, {sec.cik.nunique():,} CIKs.","",
      "## Matching limitation","The SEC series/class file is a 2010 snapshot. Annual rates use each year's Petajisto ticker/name against that snapshot; they do not prove a ticker or series/class was active in each historical year. Multiple classes within one series are separately flagged.","",
      "## Annual match rates","",annual.to_markdown(index=False),"",
      "## Filing classification","Only downloaded EDGAR prospectus/registration-statement document text is used. Enhanced-index evidence takes precedence; conflicting active/index signals and absent series-specific evidence remain unclassified. Filing URLs and evidence phrases are in sec_filing_evidence.csv. These machine-assisted labels require review before empirical use.","",
      "## Output inventory","- sec_match_by_fund_period.csv","- sec_match_by_fund_year.csv","- sec_match_candidates.csv","- sec_match_rates_by_year.csv",
      "- sec_ticker_collision_audit.csv","- petajisto_ticker_year_collision_audit.csv","- petajisto_name_collision_audit.csv","- sec_series_name_collision_audit.csv",
      "- sec_filing_evidence.csv","- sec_bridge_metrics.json"]
    (a.out/"SEC_BRIDGE_AUDIT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print(json.dumps(metrics,indent=2,default=str))

if __name__=="__main__": main()
