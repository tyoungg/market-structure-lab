#!/usr/bin/env python3
"""Date-specific test of the public Petajisto fund crosswalk against Notre Dame TR."""
import argparse, hashlib, zipfile
from pathlib import Path
import pandas as pd

def clean(s):
    return s.astype("string").str.strip().replace({"":pd.NA,"nan":pd.NA,"None":pd.NA}).str.replace(r"\.0$","",regex=True)

def period_ym(s):
    x=s.astype("string").str.strip().str.replace(r"\.0$","",regex=True)
    z=x.str.extract(r"^(\d{4})[mM]?(\d{1,2})$")
    m=pd.to_numeric(z[1],errors="coerce")
    d=pd.to_datetime(z[0]+m.astype("Int64").astype("string").str.zfill(2),format="%Y%m",errors="coerce")
    return d.dt.to_period("M").astype("string")

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tr-zip",required=True,type=Path)
    ap.add_argument("--petajisto",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.tr_zip) as z:
        csvs=[n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(csvs)!=1: raise ValueError(f"TR ZIP must contain one CSV, found {csvs}")
        with z.open(csvs[0]) as f:
            tr=pd.read_csv(f,dtype={"fundno":"string","wficn":"string"},low_memory=False)
    p=pd.read_csv(a.petajisto,dtype="string",low_memory=False)
    p.columns=[str(c).strip().lower() for c in p.columns]
    if not {"fundno","wficn","rdate","ticker","fund_name"}.issubset(p.columns):
        raise ValueError(f"Unexpected Petajisto columns: {list(p.columns)}")
    tr["fundno_key"]=clean(tr.fundno); tr["wficn_key"]=clean(tr.wficn)
    tr["period"]=period_ym(tr.ym)
    p["fundno_key"]=clean(p.fundno); p["wficn_key"]=clean(p.wficn)
    p["period"]=pd.to_datetime(p.rdate,errors="coerce").dt.to_period("M").astype("string")
    if tr.period.isna().any() or p.period.isna().all(): raise ValueError("Date parsing failed")

    pf=p.dropna(subset=["fundno_key","period"]).copy()
    pw=p.dropna(subset=["wficn_key","period"]).copy()
    fc=pf.groupby(["fundno_key","period"]).wficn_key.nunique().gt(1)
    wc=pw.groupby(["wficn_key","period"]).fundno_key.nunique().gt(1)
    pf=pf.sort_values(["fundno_key","period"]).drop_duplicates(["fundno_key","period"])
    pw=pw.sort_values(["wficn_key","period"]).drop_duplicates(["wficn_key","period"])
    byfund=tr.merge(pf[["fundno_key","period","wficn_key","ticker","fund_name"]+
                       [c for c in ["indexfund","enhanced_index","crsp_fundno"] if c in pf.columns]],
                    on=["fundno_key","period"],how="left",suffixes=("","_pet"),indicator=True)
    bywficn=tr.merge(pw[["wficn_key","period","fundno_key","ticker","fund_name"]],
                     on=["wficn_key","period"],how="left",suffixes=("","_pet"),indicator=True)
    both=byfund.loc[byfund._merge.eq("both") & byfund.wficn_key.notna()]
    agree=both.wficn_key.eq(both.wficn_key_pet)
    ambiguous=pd.MultiIndex.from_frame(byfund[["fundno_key","period"]]).isin(fc[fc].index)
    safe=byfund.loc[byfund._merge.eq("both") & ~ambiguous].copy()
    recovered=safe.wficn_key.isna() & safe.wficn_key_pet.notna()
    metrics={
      "TR_rows":int(len(tr)),"TR_unique_fundno":int(tr.fundno_key.nunique()),
      "TR_unique_wficn":int(tr.wficn_key.nunique()),"TR_missing_wficn_rows":int(tr.wficn_key.isna().sum()),
      "Petajisto_rows":int(len(p)),"Petajisto_unique_fundno":int(p.fundno_key.nunique()),
      "Petajisto_unique_wficn":int(p.wficn_key.nunique()),
      "Petajisto_date_min":str(pd.to_datetime(p.rdate,errors="coerce").min()),
      "Petajisto_date_max":str(pd.to_datetime(p.rdate,errors="coerce").max()),
      "Petajisto_columns":list(p.columns),
      "Petajisto_fundno_period_conflict_keys":int(fc.sum()),
      "Petajisto_wficn_period_conflict_keys":int(wc.sum()),
      "TR_fundno_period_matches":int(byfund._merge.eq("both").sum()),
      "TR_fundno_period_match_pct":round(float(byfund._merge.eq("both").mean()*100),2),
      "TR_wficn_period_matches":int(bywficn._merge.eq("both").sum()),
      "TR_wficn_period_match_pct":round(float(bywficn._merge.eq("both").mean()*100),2),
      "dual_match_rows_with_source_wficn":int(len(both)),
      "dual_match_wficn_agreement":int(agree.sum()),
      "dual_match_wficn_disagreement":int((~agree).sum()),
      "missing_TR_wficn_recovered_by_unique_fundno_period":int(recovered.sum()),
      "Petajisto_indexfund_flag_present":"indexfund" in p.columns,
      "Petajisto_enhanced_index_flag_present":"enhanced_index" in p.columns,
      "sha256":{"TR_zip":sha(a.tr_zip),"Petajisto_csv":sha(a.petajisto)}
    }
    pd.Series(metrics).to_json(a.out/"petajisto_bridge_metrics.json",indent=2,force_ascii=False)
    cols=["fundno_key","period","wficn_key","wficn_key_pet","ticker","fund_name"]
    cols += [c for c in ["indexfund","enhanced_index","crsp_fundno"] if c in safe.columns]
    safe[cols].drop_duplicates().to_csv(a.out/"petajisto_candidate_crosswalk.csv",index=False)
    lines=["# Petajisto public crosswalk pilot","",
      "Date-specific linkage diagnostic only; not a final active/passive classification.",
      "Only unique fundno-period matches are candidates. Review WFICN disagreements and duplicate keys.",
      "Petajisto indexfund/enhanced_index flags are evidence; unflagged funds are not automatically active.",
      "The source ends in 2009; do not extrapolate forward. Cite the Petajisto data page and Petajisto (2013).","",
      "Metrics:","",pd.Series(metrics).to_json(indent=2,force_ascii=False)]
    (a.out/"petajisto_bridge_audit.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(pd.Series(metrics).to_json(indent=2,force_ascii=False))
if __name__=="__main__": main()
