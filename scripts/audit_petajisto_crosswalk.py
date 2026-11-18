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
    malformed_rows=[]
    def repair_petajisto_row(fields):
        # The published ASCII file contains occasional unquoted commas in the
        # final fund_name field. Preserve the row by joining overflow fields
        # back into that final field, and report every repair in the audit.
        if len(fields)>15:
            malformed_rows.append({"parsed_fields":len(fields),"overflow":fields[14:]})
            return fields[:14]+[",".join(fields[14:])]
        malformed_rows.append({"parsed_fields":len(fields),"overflow":[]})
        return fields
    p=pd.read_csv(a.petajisto,dtype="string",
                  engine="python",on_bad_lines=repair_petajisto_row)
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

    # Report match rates with the Petajisto file as the denominator and restrict
    # the TR denominator to the exact period actually covered by Petajisto.
    p_fund_keys=p.dropna(subset=["fundno_key","period"])[["fundno_key","period"]].drop_duplicates()
    p_wficn_keys=p.dropna(subset=["wficn_key","period"])[["wficn_key","period"]].drop_duplicates()
    tr_fund_keys=tr.dropna(subset=["fundno_key","period"])[["fundno_key","period"]].drop_duplicates()
    tr_wficn_keys=tr.dropna(subset=["wficn_key","period"])[["wficn_key","period"]].drop_duplicates()
    pet_fund_link=p_fund_keys.merge(tr_fund_keys,on=["fundno_key","period"],how="left",indicator=True)
    pet_wficn_link=p_wficn_keys.merge(tr_wficn_keys,on=["wficn_key","period"],how="left",indicator=True)
    p_start,p_end=p.period.min(),p.period.max()
    tr_window=tr.loc[tr.period.between(p_start,p_end)].copy()
    tr_window_link=tr_window.merge(p_fund_keys,on=["fundno_key","period"],how="left",indicator=True)
    safe_both=safe.loc[safe.wficn_key.notna()]
    safe_agree=safe_both.wficn_key.eq(safe_both.wficn_key_pet)
    annual= p_fund_keys.assign(year=p_fund_keys.period.str[:4])
    annual_link=annual.merge(tr_fund_keys.assign(matched=1),on=["fundno_key","period"],how="left")
    annual_link["matched"]=annual_link["matched"].fillna(0).astype(int)
    annual_report=(annual_link.groupby("year").agg(
        petajisto_fundno_period_keys=("fundno_key","size"),
        matched_fundno_period_keys=("matched","sum"),
        petajisto_funds=("fundno_key","nunique")
    ).reset_index())
    annual_report["fundno_period_match_pct"]=(100*annual_report.matched_fundno_period_keys/
                                                annual_report.petajisto_fundno_period_keys).round(2)
    annual_funds=(annual_link.loc[annual_link.matched.eq(1)].groupby("year").fundno_key.nunique())
    annual_report["matched_funds"]=annual_report.year.map(annual_funds).fillna(0).astype(int)
    annual_report["fund_coverage_pct"]=(100*annual_report.matched_funds/
                                         annual_report.petajisto_funds).round(2)
    annual_report.to_csv(a.out/"petajisto_annual_match_rates.csv",index=False)
    metrics={
      "TR_rows":int(len(tr)),"TR_unique_fundno":int(tr.fundno_key.nunique()),
      "TR_unique_wficn":int(tr.wficn_key.nunique()),"TR_missing_wficn_rows":int(tr.wficn_key.isna().sum()),
      "Petajisto_rows":int(len(p)),"Petajisto_unique_fundno":int(p.fundno_key.nunique()),
      "Petajisto_unique_wficn":int(p.wficn_key.nunique()),
      "Petajisto_unique_fundno_period_keys":int(len(p_fund_keys)),
      "Petajisto_unique_wficn_period_keys":int(len(p_wficn_keys)),
      "Petajisto_fundno_period_keys_matched_to_TR":int(pet_fund_link._merge.eq("both").sum()),
      "Petajisto_fundno_period_key_match_pct":round(float(pet_fund_link._merge.eq("both").mean()*100),2),
      "Petajisto_distinct_funds_matched_to_TR":int(pet_fund_link.loc[pet_fund_link._merge.eq("both"),"fundno_key"].nunique()),
      "Petajisto_distinct_fund_coverage_pct":round(float(pet_fund_link.loc[pet_fund_link._merge.eq("both"),"fundno_key"].nunique()/p.fundno_key.nunique()*100),2),
      "Petajisto_wficn_period_keys_matched_to_TR":int(pet_wficn_link._merge.eq("both").sum()),
      "Petajisto_wficn_period_key_match_pct":round(float(pet_wficn_link._merge.eq("both").mean()*100),2),
      "TR_rows_in_Petajisto_observed_date_window":int(len(tr_window)),
      "TR_rows_in_window_matched_by_fundno_period":int(tr_window_link._merge.eq("both").sum()),
      "TR_window_fundno_period_match_pct":round(float(tr_window_link._merge.eq("both").mean()*100),2),
      "TR_window_start":str(p_start),
      "TR_window_end":str(p_end),
      "Petajisto_fundno_period_duplicate_rows":int(p.duplicated(["fundno_key","period"]).sum()),
      "Petajisto_date_min":str(pd.to_datetime(p.rdate,errors="coerce").min()),
      "Petajisto_date_max":str(pd.to_datetime(p.rdate,errors="coerce").max()),
      "Petajisto_columns":list(p.columns),
      "Petajisto_malformed_rows_repaired":len([x for x in malformed_rows if x["parsed_fields"]>15]),
      "Petajisto_malformed_row_examples":malformed_rows[:5],
      "Petajisto_fundno_period_conflict_keys":int(fc.sum()),
      "Petajisto_wficn_period_conflict_keys":int(wc.sum()),
      "TR_fundno_period_matches":int(byfund._merge.eq("both").sum()),
      "TR_fundno_period_match_pct":round(float(byfund._merge.eq("both").mean()*100),2),
      "TR_wficn_period_matches":int(bywficn._merge.eq("both").sum()),
      "TR_wficn_period_match_pct":round(float(bywficn._merge.eq("both").mean()*100),2),
      "dual_match_rows_with_source_wficn":int(len(both)),
      "dual_match_wficn_agreement":int(agree.sum()),
      "dual_match_wficn_disagreement":int((~agree).sum()),
      "unambiguous_dual_match_rows_with_source_wficn":int(len(safe_both)),
      "unambiguous_dual_match_wficn_agreement":int(safe_agree.sum()),
      "unambiguous_dual_match_wficn_disagreement":int((~safe_agree).sum()),
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
