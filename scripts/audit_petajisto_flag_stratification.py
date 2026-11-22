#!/usr/bin/env python3
"""C.1 source-aware stratification using Petajisto's positive fund-type flags.

This does NOT identify an active-only universe. Unflagged records remain
unclassified; unmatched TR observations remain outside the classified sample.
TR and CRSP are not pooled. The 5% and 20% Active Share floors are separate
mechanical sensitivity samples, never definitions of active management.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

BENCHMARKS = {"S&P 500": "as_s5", "Russell 1000": "as_r1"}
LINK_TYPES = {"primary_wficn_agreement", "recovered_missing_tr_wficn"}


def norm_id(s):
    return s.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)


def parse_ym(s):
    x=s.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    m=x.str.extract(r"^(\d{4})[mM]?(\d{1,2})$")
    month=pd.to_numeric(m[1],errors="coerce")
    return pd.to_datetime(m[0]+month.astype("Int64").astype("string").str.zfill(2),format="%Y%m",errors="coerce")


def summarize(df, provider, only_bench=None):
    rows=[]
    for (year, group, link_type), g in df.groupby(["year","source_class","link_type"],dropna=False):
        for bench, col in BENCHMARKS.items():
            if only_bench is not None and bench != only_bench:
                continue
            x=pd.to_numeric(g[col],errors="coerce")
            a=pd.to_numeric(g["total_assets"],errors="coerce")
            valid=x.notna()
            x=x[valid]; w=a.loc[x.index].where(a.loc[x.index].gt(0))
            aw=float((x*w).sum()/w.sum()) if w.notna().any() and w.sum()>0 else None
            rows.append({"provider":provider,"year":int(year),"source_class":group,
                         "link_type":link_type,"benchmark":bench,"observations":int(x.size),
                         "unique_funds":int(g.loc[x.index,"fundno"].nunique()),
                         "mean":float(x.mean()) if x.size else None,
                         "median":float(x.median()) if x.size else None,
                         "p10":float(x.quantile(.10)) if x.size else None,
                         "p25":float(x.quantile(.25)) if x.size else None,
                         "p75":float(x.quantile(.75)) if x.size else None,
                         "p90":float(x.quantile(.90)) if x.size else None,
                         "asset_weighted_mean":aw,
                         "assets_available_for_weighting":int(w.notna().sum()),
                         "fund_quarter_assets_sum_usd":float(w.sum()) if w.notna().any() else 0.0})
    return pd.DataFrame(rows)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--tr',required=True,type=Path)
    ap.add_argument('--crosswalk',required=True,type=Path)
    ap.add_argument('--crosswalk-metrics',type=Path)
    ap.add_argument('--out',required=True,type=Path)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    tr=pd.read_csv(a.tr,low_memory=False,dtype={"fundno":"string"})
    bridge=pd.read_csv(a.crosswalk,low_memory=False,dtype="string")
    upstream_metrics=json.loads(a.crosswalk_metrics.read_text()) if a.crosswalk_metrics else {}
    required_tr={"fundno","ym","total_assets",*BENCHMARKS.values()}
    required_b={"fundno_key","period","wficn_key","wficn_key_pet","indexfund","enhanced_index","ticker","fund_name"}
    if not required_tr.issubset(tr.columns): raise ValueError(f"TR missing {required_tr-set(tr.columns)}")
    if not required_b.issubset(bridge.columns): raise ValueError(f"Crosswalk missing {required_b-set(bridge.columns)}")
    tr["fundno_key"]=norm_id(tr.fundno); tr["date"]=parse_ym(tr.ym)
    tr["period"]=tr.date.dt.to_period('M').astype('string'); tr["year"]=tr.date.dt.year
    if tr.date.isna().any(): raise ValueError(f"TR date parse failures: {int(tr.date.isna().sum())}")
    if tr.duplicated(["fundno_key","period"]).any(): raise ValueError("TR fundno-period keys are not unique")
    bridge["fundno_key"]=norm_id(bridge.fundno_key)
    bridge["wficn_key"]=norm_id(bridge.wficn_key)
    bridge["wficn_key_pet"]=norm_id(bridge.wficn_key_pet)
    bridge["link_type"] = "excluded_wficn_disagreement"
    bridge.loc[bridge.wficn_key.isna() & bridge.wficn_key_pet.notna(),"link_type"] = "recovered_missing_tr_wficn"
    agree=bridge.wficn_key.notna() & bridge.wficn_key_pet.notna() & bridge.wficn_key.eq(bridge.wficn_key_pet)
    bridge.loc[agree,"link_type"] = "primary_wficn_agreement"
    b=bridge.loc[bridge.link_type.isin(LINK_TYPES)].copy()
    if len(bridge)!=64225: raise ValueError(f"Expected 64,225 crosswalk candidates, found {len(bridge)}")
    if int(bridge.link_type.eq('excluded_wficn_disagreement').sum())!=388: raise ValueError("Expected 388 WFICN disagreements")
    if len(b)!=63837: raise ValueError(f"Expected 63,837 eligible records, found {len(b)}")
    if upstream_metrics and int(upstream_metrics.get('Petajisto_fundno_period_conflict_keys',-1))!=67:
        raise ValueError("Upstream crosswalk audit did not report 67 ambiguous fundno-period keys")
    if b.duplicated(["fundno_key","period"]).any(): raise ValueError("Eligible crosswalk keys are not unique")
    b["indexfund"]=pd.to_numeric(b.indexfund,errors='coerce')
    b["enhanced_index"]=pd.to_numeric(b.enhanced_index,errors='coerce')
    if b[["indexfund","enhanced_index"]].isna().any().any(): raise ValueError("Missing Petajisto flags")
    if not b[["indexfund","enhanced_index"]].isin([0,1]).all().all(): raise ValueError("Petajisto flags are not binary")
    if ((b.indexfund.eq(1)) & (b.enhanced_index.eq(1))).any(): raise ValueError("Overlapping positive flags")
    b["source_class"]="unclassified_no_positive_flag"
    b.loc[b.indexfund.eq(1),"source_class"]="petajisto_pure_index_flag"
    b.loc[b.enhanced_index.eq(1),"source_class"]="petajisto_enhanced_index_flag"
    tr["total_assets"]=pd.to_numeric(tr.total_assets,errors='coerce')
    for c in BENCHMARKS.values(): tr[c]=pd.to_numeric(tr[c],errors='coerce')
    merged=tr.merge(b[["fundno_key","period","link_type","indexfund","enhanced_index","source_class","ticker","fund_name"]],
                    on=["fundno_key","period"],how='left',validate='one_to_one',indicator=True)
    matched=merged.loc[merged._merge.eq('both')].copy()
    if len(matched)!=63837: raise ValueError(f"TR matched {len(matched)} of 63,837 eligible rows")
    expected={"primary_wficn_agreement":63428,"recovered_missing_tr_wficn":409}
    if matched.link_type.value_counts().to_dict()!=expected: raise ValueError("Link-type composition differs from validated bridge")
    if matched.year.min()<1980 or matched.year.max()>2009: raise ValueError("Unexpected year outside Petajisto coverage")
    matched.to_csv(a.out/'c1_petajisto_flag_matched_panel.csv',index=False)
    annual=summarize(matched,'TR')
    annual.to_csv(a.out/'c1_annual_flag_stratification.csv',index=False)
    floor_rows=[]
    for floor in (0.0,0.05,0.20):
        for bench,col in BENCHMARKS.items():
            subset=matched.loc[pd.to_numeric(matched[col],errors='coerce').ge(floor)].copy()
            sm=summarize(subset,'TR',only_bench=bench)
            sm['floor_sample']=f'AS>={floor:.0%}'
            floor_rows.append(sm)
    floors=pd.concat(floor_rows,ignore_index=True)
    floors.to_csv(a.out/'c1_annual_flag_floor_sensitivity.csv',index=False)
    total=tr.groupby('year').agg(tr_fund_quarter_rows=('fundno','size'),tr_unique_funds=('fundno','nunique'),tr_assets=('total_assets','sum')).reset_index()
    m=matched.groupby('year').agg(matched_rows=('fundno','size'),matched_unique_funds=('fundno','nunique')).reset_index()
    cov=total.merge(m,on='year',how='left').fillna({'matched_rows':0,'matched_unique_funds':0})
    cov['matched_row_coverage_pct']=100*cov.matched_rows/cov.tr_fund_quarter_rows
    cov.to_csv(a.out/'c1_annual_match_coverage.csv',index=False)
    classes=matched.groupby(['source_class','link_type']).agg(rows=('fundno','size'),funds=('fundno','nunique'),fund_quarter_assets_sum_usd=('total_assets','sum')).reset_index()
    classes.to_csv(a.out/'c1_classification_counts.csv',index=False)
    pet_window=tr.loc[tr.year.between(1980,2009)]
    matched_funds=int(matched.fundno.nunique())
    window_rows=int(len(pet_window))
    class_counts=matched.source_class.value_counts().to_dict()
    metrics={
      'provider':'TR only','TR_rows':len(tr),'TR_year_min':int(tr.year.min()),'TR_year_max':int(tr.year.max()),
      'TR_rows_1980_2009':window_rows,'TR_unique_funds_1980_2009':int(pet_window.fundno.nunique()),
      'unmatched_TR_rows_1980_2009':int(window_rows-len(matched)),
      'matched_unique_fund_coverage_1980_2009_pct':round(100*matched_funds/pet_window.fundno.nunique(),2),
      'Petajisto_crosswalk_candidate_rows':len(bridge),'WFICN_disagreements_excluded':int(bridge.link_type.eq('excluded_wficn_disagreement').sum()),
      'upstream_ambiguous_fundno_period_keys_excluded':upstream_metrics.get('Petajisto_fundno_period_conflict_keys'),
      'Petajisto_eligible_rows':len(b),'matched_TR_rows':len(matched),'unmatched_TR_rows_all_years':int(len(tr)-len(matched)),
      'matched_row_coverage_1980_2009_pct':round(100*len(matched)/window_rows,2),
      'matched_unique_funds_1980_2009':matched_funds,
      'primary_agreements':int(matched.link_type.eq('primary_wficn_agreement').sum()),
      'separate_recoveries':int(matched.link_type.eq('recovered_missing_tr_wficn').sum()),
      'positive_pure_index_flags':int(matched.indexfund.eq(1).sum()),
      'positive_enhanced_index_flags':int(matched.enhanced_index.eq(1).sum()),
      'neither_positive_flag_unclassified':int(matched.source_class.eq('unclassified_no_positive_flag').sum()),
      'source_class_row_shares_pct':{k:round(100*v/len(matched),2) for k,v in class_counts.items()},
      'flag_overlap':int((matched.indexfund.eq(1)&matched.enhanced_index.eq(1)).sum()),
      'matched_missing_as_s5':int(matched.as_s5.isna().sum()),'matched_missing_as_r1':int(matched.as_r1.isna().sum()),
      'classification_scope':'positive source flags only; no-positive-flag records remain unclassified',
      'unmatched_scope':'not linked to the Petajisto-TR bridge; no strategy label assigned',
      'floor_definition':'within each benchmark, retain observations with Active Share >= 0%, 5%, or 20%; floors are sensitivity samples, not strategy classifiers',
      'TR_CRSP_pooled':False,
      'note':'Petajisto flags cover 1980-2009; no extrapolation beyond that window. Asset sums are fund-quarter TNA sums, not unique AUM.'}
    (a.out/'c1_flag_stratification_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    print(json.dumps(metrics,indent=2))


if __name__=='__main__':
    main()
