#!/usr/bin/env python3
"""Build an auditable fund-year ledger from frozen SEC identity and filing artifacts."""
import argparse, hashlib, json, shutil
from pathlib import Path
import pandas as pd

KEY = ["cik_norm", "series_id_norm"]

def read(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)

def ids(s, width=None):
    x = s.astype("string").fillna("").str.strip().replace({"nan":"", "None":"", "<NA>":""})
    return x if width is None else x.where(x.eq(""), x.str.replace(r"\.0$","",regex=True).str.zfill(width))

def dates(s):
    return pd.to_datetime(s.replace("", pd.NA), format="mixed", errors="coerce")

def item69_candidate(flag):
    return {"Y":"passive_index_candidate", "N":"not_reported_as_index_not_active"}.get(str(flag), "unclassified_invalid_response")

def nsar_eligible(filing, report, cutoff):
    if pd.isna(filing) or pd.isna(report): return False
    age = (cutoff-report).days
    return filing < cutoff and report < cutoff and 0 <= age <= 548

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def require(df, cols, name):
    missing=sorted(set(cols)-set(df.columns))
    if missing: raise ValueError(f"{name} missing columns: {missing}")

def build(a):
    out=a.out; out.mkdir(parents=True,exist_ok=True)
    fy, p, n, nsar_asof, h = map(read,[a.fund_year_csv,a.prospectus_evidence_csv,a.nsar_evidence_csv,a.nsar_asof_csv,a.nsar_header_matches_csv])
    require(fy,["fundno_key","year","series_match_status","matched_series_id","matched_cik","matched_series_name","share_class_ambiguous","link_type","sampled_registry_series_match","indexfund","enhanced_index"],"fund-year")
    require(p,["cik","series_id","series_name","filing_date","form","accession","filing_url","classification","evidence_phrases","evidence_context"],"prospectus")
    require(n,["cik","series_id","index_fund_flag","filing_date","report_date","form","accession","submission_url","answer_filename"],"Item 69")
    require(nsar_asof,["fundno_key","year","nsar_index_fund_status"],"Item 69 as-of")
    require(h,["cik","series_id","historical_header_series_name","filing_date","report_date","form","accession","submission_url","series_name_exact_match","header_class_count","header_class_ids"],"N-SAR header")

    if fy.duplicated(["fundno_key","year"]).any(): raise ValueError("Duplicate fundno/year rows")
    fy["fund_year"]=pd.to_numeric(fy.year,errors="coerce")
    if fy.fund_year.isna().any(): raise ValueError("Unparseable fund-year")
    fy.fund_year=fy.fund_year.astype(int)
    fy["cik_norm"]=ids(fy.matched_cik,10); fy["series_id_norm"]=ids(fy.matched_series_id)
    fy["unique_series_link"]=fy.series_match_status.eq("unique_series") & fy.cik_norm.ne("") & fy.series_id_norm.ne("")
    fy["asof_cutoff"]=pd.to_datetime(fy.fund_year.astype(str)+"-01-01")
    fy["registry_indexfund_flag"]=fy.indexfund
    fy["registry_enhanced_index_flag"]=fy.enhanced_index
    fy["registry_strategy_class_candidate"]=fy.get("strategy_class",pd.Series([""]*len(fy)))

    # Tier 1: prospectus filing evidence; preserve age, do not impose an unregistered expiry.
    p=p.copy(); p["cik_norm"]=ids(p.cik,10); p["series_id_norm"]=ids(p.series_id)
    p["filing_date_dt"]=dates(p.filing_date); p["report_date_dt"]=pd.NaT
    p["source_tier"]="1"; p["source_type"]="SEC_prospectus_or_related_filing"
    p["raw_response"]=""; p["item69_coordinate"]=""; p["item69_coordinate_source_status"]="not_applicable"
    p["candidate_class"]=p.classification; p["candidate_reason"]=p.evidence_phrases
    p["evidence_url"]=p.filing_url; p["evidence_text"]=p.evidence_context
    p["review_status"]=p.classification.map(lambda x:"unreviewed_automated_candidate" if x and x!="unclassified" else "not_positively_classified_by_extractor")

    # Tier 2: series-level N-SAR Item 69; N is not active.
    n=n.copy(); n["cik_norm"]=ids(n.cik,10); n["series_id_norm"]=ids(n.series_id)
    n["filing_date_dt"]=dates(n.filing_date); n["report_date_dt"]=dates(n.report_date)
    n["source_tier"]="2"; n["source_type"]="SEC_N-SAR_Item_69_series_response"
    n["raw_response"]=n.index_fund_flag; n["item69_coordinate"]=""
    n["item69_coordinate_source_status"]="not_present_in_existing_item69_artifact"
    n["candidate_class"]=n.index_fund_flag.map(item69_candidate)
    n["candidate_reason"]="Item 69 response="+n.index_fund_flag
    n["evidence_url"]=n.submission_url
    n["evidence_text"]="Item 69="+n.index_fund_flag+"; answer document="+n.answer_filename
    n["review_status"]="structured_questionnaire_evidence_pending_cross_source_review"

    # Tier 3: SEC-HEADER series IDs are identity-only, not strategy evidence.
    h=h.copy(); h["cik_norm"]=ids(h.cik,10); h["series_id_norm"]=ids(h.series_id)
    h["filing_date_dt"]=dates(h.filing_date); h["report_date_dt"]=dates(h.report_date)
    h["source_tier"]="3"; h["source_type"]="SEC_N-SAR_header_series_identity"
    h["raw_response"]=""; h["item69_coordinate"]=""; h["item69_coordinate_source_status"]="not_applicable"
    h["candidate_class"]="identity_only_not_strategy"
    h["candidate_reason"]="historical SEC submission header identifies target series ID"
    h["evidence_url"]=h.submission_url
    h["evidence_text"]="header_name="+h.historical_header_series_name.astype(str)+"; exact="+h.series_name_exact_match.astype(str)+"; classes="+h.header_class_ids.astype(str)
    h["review_status"]="identity_evidence_only_not_strategy_review"

    common=["cik_norm","series_id_norm","source_tier","source_type","filing_date","filing_date_dt","report_date","report_date_dt","form","accession","evidence_url","evidence_text","candidate_class","candidate_reason","review_status","raw_response","item69_coordinate","item69_coordinate_source_status"]
    p["report_date"]=""; frames=[p,n,h]
    for d in frames:
        for c in common:
            if c not in d: d[c]=""
    events=pd.concat([d[common] for d in frames],ignore_index=True)
    events["evidence_event_id"]=events.apply(lambda r:f"{r.source_tier}:{r.accession}:{r.series_id_norm}",axis=1)
    events=events.drop_duplicates(["evidence_event_id","cik_norm"])

    linked=fy.loc[fy.unique_series_link,["fundno_key","fund_year","asof_cutoff","cik_norm","series_id_norm","matched_series_name","link_type","share_class_ambiguous"]]
    items=linked.merge(events,on=KEY,how="inner",validate="many_to_many")
    items["evidence_age_days"]=(items.asof_cutoff-items.filing_date_dt).dt.days
    items["report_age_days"]=(items.asof_cutoff-items.report_date_dt).dt.days
    items["filing_precedes_cutoff"]=items.filing_date_dt.notna() & (items.filing_date_dt<items.asof_cutoff)
    items["report_precedes_cutoff"]=items.report_date_dt.notna() & (items.report_date_dt<items.asof_cutoff)
    is_n=items.source_type.eq("SEC_N-SAR_Item_69_series_response")
    is_h=items.source_type.eq("SEC_N-SAR_header_series_identity")
    is_p=items.source_type.eq("SEC_prospectus_or_related_filing")
    items["asof_eligible"]=items.filing_precedes_cutoff
    items.loc[is_n,"asof_eligible"]=[nsar_eligible(f,r,c) for f,r,c in zip(items.loc[is_n,"filing_date_dt"],items.loc[is_n,"report_date_dt"],items.loc[is_n,"asof_cutoff"])]
    items["temporal_exclusion_reason"]=""
    items.loc[items.filing_date_dt.isna(),"temporal_exclusion_reason"]="missing_or_unparseable_filing_date"
    items.loc[items.filing_date_dt.notna() & ~items.filing_precedes_cutoff,"temporal_exclusion_reason"]="filed_on_or_after_fund_year_cutoff"
    items.loc[is_n & items.filing_precedes_cutoff & ~items.report_precedes_cutoff,"temporal_exclusion_reason"]="N-SAR_report_date_missing_or_not_prior_to_cutoff"
    items.loc[is_n & items.filing_precedes_cutoff & items.report_precedes_cutoff & ~items.report_age_days.between(0,548,inclusive="both"),"temporal_exclusion_reason"]="N-SAR_report_period_older_than_548_days"
    items["prospectus_staleness_bucket"]="not_applicable"
    items.loc[is_p & items.evidence_age_days.between(0,365),"prospectus_staleness_bucket"]="0_365_days"
    items.loc[is_p & items.evidence_age_days.between(366,730),"prospectus_staleness_bucket"]="366_730_days"
    items.loc[is_p & items.evidence_age_days.gt(730),"prospectus_staleness_bucket"]="over_730_days"
    items.loc[is_p & items.evidence_age_days.lt(0),"prospectus_staleness_bucket"]="future_excluded"

    # Recompute the N-SAR as-of status from raw events; reconcile against the frozen prior panel.
    latest={}
    for key,g in items.loc[is_n & items.asof_eligible].groupby(["fundno_key","fund_year"]):
        d=g.filing_date_dt.max(); last=g[g.filing_date_dt.eq(d)]; flags=sorted(set(last.raw_response.astype(str)))
        latest[key]={"latest_nsar_filing_date":d.date().isoformat(),"latest_nsar_report_date":"|".join(sorted(set(last.report_date.astype(str)))),"latest_nsar_accessions":"|".join(sorted(set(last.accession.astype(str)))),"latest_nsar_flag":flags[0] if len(flags)==1 else "CONFLICT","latest_nsar_same_date_flag_count":len(flags)}
    src=nsar_asof[["fundno_key","year","nsar_index_fund_status"]].copy(); src["fund_year"]=pd.to_numeric(src.year,errors="coerce")
    srcmap={(r.fundno_key,int(r.fund_year)):r.nsar_index_fund_status for r in src.dropna(subset=["fund_year"]).itertuples()}

    pa=items.loc[is_p & items.asof_eligible]
    ps=pa.groupby(["fundno_key","fund_year"]).agg(prospectus_asof_evidence_events=("evidence_event_id","nunique"),prospectus_latest_filing_date=("filing_date_dt","max"),prospectus_active_candidate_events=("candidate_class",lambda x:int(x.eq("active").sum())),prospectus_unclassified_events=("candidate_class",lambda x:int(x.eq("unclassified").sum()))).reset_index()
    sm=items.groupby(["fundno_key","fund_year"]).agg(all_linked_evidence_events=("evidence_event_id","nunique"),all_linked_prospectus_events=("source_type",lambda x:int(x.eq("SEC_prospectus_or_related_filing").sum())),all_linked_nsar_events=("source_type",lambda x:int(x.eq("SEC_N-SAR_Item_69_series_response").sum())),all_linked_nsar_header_events=("source_type",lambda x:int(x.eq("SEC_N-SAR_header_series_identity").sum())),asof_eligible_evidence_events=("asof_eligible","sum")).reset_index()
    fy=fy.merge(sm,on=["fundno_key","fund_year"],how="left",validate="one_to_one").merge(ps,on=["fundno_key","fund_year"],how="left",validate="one_to_one")
    countcols=["all_linked_evidence_events","all_linked_prospectus_events","all_linked_nsar_events","all_linked_nsar_header_events","asof_eligible_evidence_events","prospectus_asof_evidence_events","prospectus_active_candidate_events","prospectus_unclassified_events"]
    for c in countcols:
        if c not in fy: fy[c]=0
        fy[c]=pd.to_numeric(fy[c],errors="coerce").fillna(0).astype(int)
    for c in ["latest_nsar_filing_date","latest_nsar_report_date","latest_nsar_accessions","latest_nsar_flag"]: fy[c]=""
    fy["latest_nsar_same_date_flag_count"]=0
    for i,r in fy.iterrows():
        for c,v in latest.get((r.fundno_key,int(r.fund_year)),{}).items(): fy.at[i,c]=v

    def nsar_status(r):
        if str(r.sampled_registry_series_match).lower() not in {"true","1"}: return "unclassified_CIK_not_in_N-SAR_sample"
        if not r.cik_norm: return "unclassified_no_CIK"
        if not r.unique_series_link: return "unclassified_no_unique_SEC_series"
        if not r.latest_nsar_flag: return "unclassified_no_recent_prior_N-SAR"
        return {"Y":"n_sar_index_fund_yes","N":"n_sar_index_fund_no_not_active","CONFLICT":"unclassified_conflicting_item69"}.get(r.latest_nsar_flag,"unclassified_item69_value")
    fy["nsar_index_fund_status_recomputed"]=fy.apply(nsar_status,axis=1)
    fy["nsar_index_fund_status_source"]=fy.apply(lambda r:srcmap.get((r.fundno_key,int(r.fund_year)),""),axis=1)
    fy["nsar_status_reconciles_to_prior_artifact"]=fy.nsar_index_fund_status_recomputed.eq(fy.nsar_index_fund_status_source)

    fy["candidate_class"]=""; fy["candidate_class_basis"]=""; fy["classification_review_status"]="unreviewed_unclassified"
    yes=fy.nsar_index_fund_status_recomputed.eq("n_sar_index_fund_yes")
    no=fy.nsar_index_fund_status_recomputed.eq("n_sar_index_fund_no_not_active")
    fy.loc[yes,"candidate_class"]="passive_index_candidate"; fy.loc[yes,"candidate_class_basis"]="series_specific_N-SAR_Item69_Y"; fy.loc[yes,"classification_review_status"]="needs_cross_source_strategy_document_review"
    fy.loc[no,"candidate_class_basis"]="Item69_N_is_not_active_evidence"
    active=fy.prospectus_active_candidate_events.gt(0)
    fy.loc[active,"candidate_class"]="active_candidate_unreviewed"; fy.loc[active,"candidate_class_basis"]="automated_prospectus_phrase_extraction_requires_manual_validation"; fy.loc[active,"classification_review_status"]="manual_review_required_no_active_label"
    conflict=yes & active
    fy.loc[conflict,"candidate_class"]="conflicting_candidates"; fy.loc[conflict,"candidate_class_basis"]="N-SAR_Y_and_unreviewed_prospectus_active_candidate"; fy.loc[conflict,"classification_review_status"]="conflict_manual_adjudication_required"
    fy["final_class"]="unclassified"; fy["final_class_reason"]="no_manual_adjudication_in_existing_artifacts"
    fy.loc[yes & ~active,"final_class_reason"]="N-SAR_Y_is_positive_index_evidence_but_requires_document_review"
    fy.loc[no,"final_class_reason"]="N-SAR_N_is_not_active_evidence"
    fy.loc[active,"final_class_reason"]="automated_prospectus_candidate_not_manually_validated"
    fy.loc[conflict,"final_class_reason"]="conflicting_or_unreviewed_evidence_requires_adjudication"

    itemcols=["fundno_key","fund_year","cik_norm","series_id_norm","matched_series_name","link_type","share_class_ambiguous","evidence_event_id","source_tier","source_type","form","accession","filing_date","report_date","evidence_url","evidence_text","raw_response","item69_coordinate","item69_coordinate_source_status","candidate_class","candidate_reason","review_status","evidence_age_days","report_age_days","filing_precedes_cutoff","report_precedes_cutoff","asof_eligible","temporal_exclusion_reason","prospectus_staleness_bucket"]
    items[itemcols].to_csv(out/"fund_year_evidence_items.csv",index=False)
    fy.to_csv(out/"fund_year_evidence_ledger.csv",index=False)
    p.loc[p.classification.ne("unclassified")].assign(review_status="manual_review_required_unreviewed_candidate",final_class="unclassified_pending_manual_review").to_csv(out/"prospectus_candidate_review_queue.csv",index=False)
    for src,dest in [(a.nsar_registrant_csv,"nsar_registrant_level_unassigned.csv"),(a.nsar_unmatched_csv,"nsar_unmatched_item7_evidence.csv"),(a.nsar_errors_csv,"nsar_item69_retrieval_errors.csv"),(a.nsar_api_errors_csv,"nsar_header_api_errors.csv"),(a.nsar_manifest_csv,"nsar_header_processing_manifest.csv")]:
        if src and Path(src).exists(): shutil.copyfile(src,out/dest)
    n[["cik","series_id","accession","filing_date","report_date","index_fund_flag"]].assign(item69_coordinate="",coordinate_status="not_present_in_existing_item69_artifact").to_csv(out/"nsar_item69_coordinate_gap.csv",index=False)

    inv=events.groupby(["cik_norm","series_id_norm","source_tier","source_type"]).agg(evidence_events=("evidence_event_id","nunique"),first_filing_date=("filing_date_dt","min"),last_filing_date=("filing_date_dt","max"),candidate_classes=("candidate_class",lambda x:"|".join(sorted(set(x.astype(str)))))).reset_index()
    inv.to_csv(out/"series_evidence_inventory.csv",index=False)
    annual=[]
    for year,g in fy.groupby("fund_year"):
        annual.append({"year":int(year),"fund_year_rows":len(g),"unique_fundnos":g.fundno_key.nunique(),"unique_series_link_rows":int(g.unique_series_link.sum()),"multiple_series_ambiguous_rows":int(g.series_match_status.eq("multiple_series_ambiguous").sum()),"no_strict_candidate_rows":int(g.series_match_status.eq("no_strict_candidate").sum()),"sampled_unique_series_rows":int((g.unique_series_link & g.sampled_registry_series_match.astype(str).str.lower().isin(["true","1"])).sum()),"fund_years_with_prior_prospectus_evidence":int(g.prospectus_asof_evidence_events.gt(0).sum()),"prior_prospectus_evidence_events":int(g.prospectus_asof_evidence_events.sum()),"fund_years_with_prior_nsar_header_identity":int(g.all_linked_nsar_header_events.gt(0).sum()),"prior_nsar_header_identity_events":int(g.all_linked_nsar_header_events.sum()),"prior_automated_active_candidates":int(g.prospectus_active_candidate_events.sum()),"n_sar_item69_yes":int(g.nsar_index_fund_status_recomputed.eq("n_sar_index_fund_yes").sum()),"n_sar_item69_no_not_active":int(g.nsar_index_fund_status_recomputed.eq("n_sar_index_fund_no_not_active").sum()),"n_sar_unclassified":int(g.nsar_index_fund_status_recomputed.str.startswith("unclassified").sum()),"final_unclassified":int(g.final_class.eq("unclassified").sum())})
    pd.DataFrame(annual).to_csv(out/"fund_year_evidence_annual_coverage.csv",index=False)

    metrics={"fund_year_rows":len(fy),"fund_year_unique_keys":len(fy[["fundno_key","fund_year"]].drop_duplicates()),"duplicate_fund_year_keys":int(fy.duplicated(["fundno_key","fund_year"]).sum()),"fundnos":int(fy.fundno_key.nunique()),"year_min":int(fy.fund_year.min()),"year_max":int(fy.fund_year.max()),"series_match_status_counts":{str(k):int(v) for k,v in fy.series_match_status.value_counts().items()},"unique_series_link_rows":int(fy.unique_series_link.sum()),"share_class_ambiguous_rows":int(fy.share_class_ambiguous.astype(str).str.lower().isin(["true","1"]).sum()),"sampled_unique_series_rows":int((fy.unique_series_link & fy.sampled_registry_series_match.astype(str).str.lower().isin(["true","1"])).sum()),"prospectus_source_rows":len(p),"prospectus_source_series":int(p.series_id.nunique()),"nsar_source_rows":len(n),"nsar_source_series":int(n.series_id.nunique()),"nsar_header_identity_source_rows":len(h),"nsar_header_identity_source_series":int(h.series_id.nunique()),"nsar_item69_coordinate_available_in_source_artifact":False,"nsar_item69_coordinate_gap_rows":len(n),"evidence_event_rows":len(events),"fund_year_evidence_item_rows":len(items),"asof_eligible_evidence_item_rows":int(items.asof_eligible.sum()),"asof_prospectus_evidence_item_rows":int((is_p & items.asof_eligible).sum()),"asof_nsar_evidence_item_rows":int((is_n & items.asof_eligible).sum()),"asof_nsar_header_identity_item_rows":int((is_h & items.asof_eligible).sum()),"nsar_reconciliation_mismatches":int((~fy.nsar_status_reconciles_to_prior_artifact).sum()),"nsar_recomputed_status_counts":{str(k):int(v) for k,v in fy.nsar_index_fund_status_recomputed.value_counts().items()},"candidate_class_counts":{str(k):int(v) for k,v in fy.candidate_class.replace("","(none)").value_counts().items()},"final_class_counts":{str(k):int(v) for k,v in fy.final_class.value_counts().items()},"active_candidate_fund_year_rows":int(active.sum()),"final_active_rows":int(fy.final_class.isin(["active_large_cap_core","other_active_style"]).sum()),"method_boundary":"No automated active candidate is promoted. Item 69 N is not active evidence. Item 69 Y is a provisional passive-index candidate and remains unclassified pending cross-source/manual adjudication.","prospectus_staleness":"No universal expiry imposed; age retained for predeclared sensitivity analysis.","source_sha256":{"fund_year_csv":digest(a.fund_year_csv),"prospectus_evidence_csv":digest(a.prospectus_evidence_csv),"nsar_evidence_csv":digest(a.nsar_evidence_csv),"nsar_asof_csv":digest(a.nsar_asof_csv),"nsar_header_matches_csv":digest(a.nsar_header_matches_csv)}}
    (out/"fund_year_evidence_ledger_metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
    report=["# Fund-Year Evidence Ledger Audit","","**Status:** Evidence ledger assembled; no active-only panel validated.","","## Key boundary",metrics["method_boundary"],"","## Metrics",json.dumps(metrics,indent=2),"","## Interpretation","All final_class values remain unclassified pending manual adjudication. Item 69 Y is a passive-index candidate; Item 69 N is not active evidence. The five automated prospectus active candidates remain unreviewed. SEC 2010 registry fields are linkage/context only. Effective dates are absent. The original Item 69 coordinate was omitted from the source artifact and is left blank rather than reconstructed.",""]
    (out/"FUND_YEAR_EVIDENCE_LEDGER_AUDIT.md").write_text("\n".join(report))

    assert len(fy)==22280 and fy.duplicated(["fundno_key","fund_year"]).sum()==0
    assert int(fy.final_class.isin(["active_large_cap_core","other_active_style"]).sum())==0
    assert int(fy.nsar_index_fund_status_recomputed.eq("n_sar_index_fund_no_not_active").sum())==181
    assert int(fy.nsar_index_fund_status_recomputed.eq("n_sar_index_fund_yes").sum())==9
    assert metrics["nsar_reconciliation_mismatches"]==0,metrics["nsar_reconciliation_mismatches"]
    assert int(p.classification.eq("active").sum())==5
    print(json.dumps(metrics,indent=2))

def main():
    ap=argparse.ArgumentParser()
    for name in ["fund-year-csv","prospectus-evidence-csv","nsar-evidence-csv","nsar-asof-csv","nsar-header-matches-csv"]:
        ap.add_argument("--"+name,required=True,type=Path)
    for name in ["nsar-registrant-csv","nsar-unmatched-csv","nsar-errors-csv","nsar-api-errors-csv","nsar-manifest-csv"]:
        ap.add_argument("--"+name,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    build(ap.parse_args())

if __name__=="__main__": main()
