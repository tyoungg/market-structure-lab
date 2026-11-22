#!/usr/bin/env python3
"""Bounded historical N-SAR series/class-header linkage feasibility audit."""
import argparse, json, os, re, time
from pathlib import Path
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

MIN_YEAR, MAX_YEAR, DELAY, MAX_PREFIX = 1994, 2018, 0.12, 262144
DEADLINE = None
FORMS = {"NSAR-A", "NSAR-B", "NSAR-AT", "NSAR-BT"}
PRIORITY = {"NSAR-B": 0, "NSAR-A": 1, "NSAR-BT": 2, "NSAR-AT": 3}


def make_session():
    email = os.environ.get("SEC_CONTACT_EMAIL", "").strip()
    if not email:
        raise RuntimeError("SEC_CONTACT_EMAIL secret is required")
    s = requests.Session()
    retry = Retry(total=2, connect=2, read=2, status=2, backoff_factor=.5,
                  status_forcelist=[408, 429, 500, 502, 503, 504],
                  allowed_methods=frozenset(["GET"]), respect_retry_after_header=False,
                  raise_on_status=False)
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "The Rational Coward Research Project (tyoungg/market-structure-lab; contact " + email + ")",
                      "Accept-Encoding": "gzip, deflate", "Connection": "keep-alive"})
    return s


def get(s, url, **kwargs):
    if DEADLINE is not None and time.monotonic() >= DEADLINE:
        raise TimeoutError("N-SAR audit reached script deadline")
    time.sleep(DELAY)
    r = s.get(url, timeout=(10, 25), **kwargs)
    r.raise_for_status()
    if DEADLINE is not None and time.monotonic() >= DEADLINE:
        r.close()
        raise TimeoutError("N-SAR audit reached script deadline")
    return r


def load_history(s, cik):
    payload = get(s, f"https://data.sec.gov/submissions/CIK{str(cik).zfill(10)}.json").json()
    frames = []
    recent = pd.DataFrame(payload.get("filings", {}).get("recent", {}))
    if not recent.empty:
        frames.append(recent)
    for item in payload.get("filings", {}).get("files", []) or []:
        lo = pd.to_datetime(item.get("filingFrom"), errors="coerce")
        hi = pd.to_datetime(item.get("filingTo"), errors="coerce")
        if pd.isna(lo) or pd.isna(hi) or hi.year < MIN_YEAR or lo.year > MAX_YEAR:
            continue
        name = item.get("name")
        if name:
            frame = pd.DataFrame(get(s, "https://data.sec.gov/submissions/" + name).json())
            if not frame.empty:
                frames.append(frame)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True, sort=False)
    return out.drop_duplicates("accessionNumber") if "accessionNumber" in out else out


def select_filings(hist):
    needed = {"filingDate", "form", "accessionNumber"}
    if hist.empty or not needed.issubset(hist.columns):
        return pd.DataFrame()
    x = hist.copy()
    x["filingDate"] = pd.to_datetime(x.filingDate, errors="coerce")
    x["form"] = x.form.astype(str).str.upper()
    x = x[x.form.isin(FORMS) & x.filingDate.dt.year.between(MIN_YEAR, MAX_YEAR)].copy()
    if x.empty:
        return x
    x["year"] = x.filingDate.dt.year
    x["priority"] = x.form.map(PRIORITY).fillna(9)
    x = x.sort_values(["year", "priority", "filingDate", "accessionNumber"],
                      ascending=[True, True, False, True])
    return x.drop_duplicates("year", keep="first")


def parse_header(s, cik, accession):
    acc = str(accession).replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{accession}.txt"
    r = get(s, url, headers={"Range": f"bytes=0-{MAX_PREFIX-1}"}, stream=True)
    chunks, size = [], 0
    try:
        for chunk in r.iter_content(65536):
            if not chunk:
                continue
            n = min(len(chunk), MAX_PREFIX-size)
            chunks.append(chunk[:n])
            size += n
            if size >= MAX_PREFIX:
                break
    finally:
        r.close()
    raw = b"".join(chunks).decode("utf-8", errors="replace")
    m = re.search(r"(?is)<SEC-HEADER>(.*?)</SEC-HEADER>", raw)
    if not m:
        raise ValueError("SEC-HEADER not found in bounded prefix")
    h = m.group(1)
    rows = []
    for sm in re.finditer(r"(?is)<SERIES>(.*?)(?=</SERIES>|<SERIES>)", h):
        block = sm.group(1)
        sid = re.search(r"(?is)<SERIES-ID>\s*(S\d{9})", block)
        nm = re.search(r"(?is)<SERIES-NAME>\s*(.*?)\s*(?=<|$)", block)
        if sid:
            classes = sorted(set(re.findall(r"(?is)<CLASS-CONTRACT-ID>\s*(C\d{9})", block)))
            rows.append({"series_id": sid.group(1),
                         "series_name": re.sub(r"\s+", " ", nm.group(1)).strip() if nm else "",
                         "class_ids": "|".join(classes), "class_count": len(classes)})
    return {"url": url, "series_rows": rows,
            "series_ids": sorted(set(re.findall(r"\bS\d{9}\b", h))),
            "class_ids": sorted(set(re.findall(r"\bC\d{9}\b", h))),
            "has_series_section": "<SERIES>" in h.upper(),
            "has_series_class_section": "<SERIES-AND-CLASSES-CONTRACTS-DATA>" in h.upper()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series-csv", required=True, type=Path)
    ap.add_argument("--candidate-csv", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--max-runtime-minutes", type=int, default=25)
    a = ap.parse_args()
    global DEADLINE
    started = time.monotonic()
    DEADLINE = started + a.max_runtime_minutes * 60
    a.out.mkdir(parents=True, exist_ok=True)
    series = pd.read_csv(a.series_csv, dtype=str, keep_default_na=False)
    candidates = pd.read_csv(a.candidate_csv, dtype=str, keep_default_na=False)
    required = {"cik", "series_id", "series_name", "first_observed_year", "last_observed_year"}
    if not required.issubset(series.columns) or "cik" not in candidates:
        raise ValueError("Prior SEC artifact input schema mismatch")
    sampled = sorted(set(candidates.cik.astype(str).str.zfill(10)))
    targets = series[series.cik.astype(str).str.zfill(10).isin(sampled)].copy()
    if len(sampled) != 80:
        raise ValueError(f"Expected prior 80-CIK sample, found {len(sampled)}")
    if targets.series_id.duplicated().any():
        raise ValueError("Duplicate target series IDs in sampled input")
    target_by_cik = {c: g for c, g in targets.groupby(targets.cik.astype(str).str.zfill(10))}
    s = make_session()
    filing_rows, match_rows, errors, cik_rows = [], [], [], []
    completed, timed_out = 0, False
    for i, cik in enumerate(sampled, 1):
        if time.monotonic() >= DEADLINE:
            timed_out = True
            break
        print(f"[{i}/{len(sampled)}] CIK {cik}", flush=True)
        cik_started = time.monotonic()
        try:
            history = load_history(s, cik)
        except Exception as e:
            errors.append({"cik": cik, "stage": "submissions_history", "error": f"{type(e).__name__}:{e}"})
            cik_rows.append({"cik": cik, "status": "history_error", "selected_filings": 0, "elapsed_seconds": round(time.monotonic()-cik_started, 2)})
            pd.DataFrame(cik_rows).to_csv(a.out/"nsar_cik_processing_manifest_checkpoint.csv", index=False)
            continue
        chosen = select_filings(history)
        target = target_by_cik.get(cik, pd.DataFrame())
        target_ids = set(target.series_id.astype(str))
        print(f"  {len(chosen)} selected N-SAR filings", flush=True)
        for f in chosen.to_dict("records"):
            if time.monotonic() >= DEADLINE:
                timed_out = True
                break
            accession, form = str(f.get("accessionNumber", "")), str(f.get("form", "")).upper()
            filed = pd.to_datetime(f.get("filingDate"), errors="coerce")
            report = pd.to_datetime(f.get("reportDate"), errors="coerce")
            row = {"cik": cik, "accession": accession, "form": form,
                   "filing_date": str(filed.date()) if pd.notna(filed) else "",
                   "report_date": str(report.date()) if pd.notna(report) else "",
                   "filing_year": int(filed.year) if pd.notna(filed) else None,
                   "target_series_count": len(target_ids), "header_series_count": 0,
                   "target_series_matches": 0, "header_class_count": 0,
                   "header_has_series_section": False, "header_has_series_and_classes": False,
                   "status": "", "submission_url": ""}
            try:
                parsed = parse_header(s, cik, accession)
                row.update({"header_series_count": len(parsed["series_ids"]),
                            "header_class_count": len(parsed["class_ids"]),
                            "header_has_series_section": parsed["has_series_section"],
                            "header_has_series_and_classes": parsed["has_series_class_section"],
                            "target_series_matches": len(target_ids.intersection(parsed["series_ids"])),
                            "submission_url": parsed["url"]})
                row["status"] = ("target_series_id_found" if row["target_series_matches"] else
                                 "series_ids_present_no_target_match" if parsed["series_ids"] else
                                 "no_series_ids_in_header")
                by_id = {x["series_id"]: x for x in parsed["series_rows"]}
                for sid in sorted(target_ids.intersection(parsed["series_ids"])):
                    t = target.loc[target.series_id.eq(sid)].iloc[0]
                    h = by_id.get(sid, {})
                    hn, tn = str(h.get("series_name", "")), str(t.series_name)
                    match_rows.append({
                        "cik": cik, "series_id": sid, "registry_series_name": tn,
                        "historical_header_series_name": hn,
                        "series_name_exact_match": bool(hn and hn.casefold() == tn.casefold()),
                        "header_class_count": h.get("class_count", 0),
                        "header_class_ids": h.get("class_ids", ""),
                        "filing_date": row["filing_date"], "report_date": row["report_date"],
                        "form": form, "accession": accession, "submission_url": parsed["url"],
                        "first_observed_year": t.first_observed_year,
                        "last_observed_year": t.last_observed_year,
                        "filing_precedes_first_observed_year": bool(
                            pd.notna(filed) and str(t.first_observed_year).isdigit()
                            and filed.year < int(t.first_observed_year))})
            except Exception as e:
                row["status"] = "header_error"
                errors.append({"cik": cik, "accession": accession, "stage": "submission_header",
                               "error": f"{type(e).__name__}:{e}"})
            filing_rows.append(row)
        completed += 1
        cik_rows.append({"cik": cik, "status": "completed", "selected_filings": len(chosen), "elapsed_seconds": round(time.monotonic()-cik_started, 2)})
        pd.DataFrame(cik_rows).to_csv(a.out/"nsar_cik_processing_manifest_checkpoint.csv", index=False)
        pd.DataFrame(filing_rows).to_csv(a.out/"nsar_filing_headers_checkpoint.csv", index=False)
        pd.DataFrame(match_rows).to_csv(a.out/"nsar_target_series_matches_checkpoint.csv", index=False)
        if timed_out:
            break
    filings, matches = pd.DataFrame(filing_rows), pd.DataFrame(match_rows)
    filings.to_csv(a.out/"nsar_filing_headers.csv", index=False)
    matches.to_csv(a.out/"nsar_target_series_matches.csv", index=False)
    pd.DataFrame(errors).to_csv(a.out/"nsar_api_errors.csv", index=False)
    pd.DataFrame(cik_rows).to_csv(a.out/"nsar_cik_processing_manifest.csv", index=False)
    summary = targets.copy()
    if not matches.empty:
        agg = matches.groupby("series_id").agg(
            nsar_header_filings=("accession", "nunique"),
            first_nsar_header_filing=("filing_date", "min"),
            last_nsar_header_filing=("filing_date", "max"),
            exact_name_matches=("series_name_exact_match", "sum"),
            header_name_rows=("historical_header_series_name", lambda x: int(x.astype(str).str.len().gt(0).sum())),
            filings_pre_first_observed_year=("filing_precedes_first_observed_year", "sum")).reset_index()
        summary = summary.merge(agg, on="series_id", how="left")
    for c in ["nsar_header_filings", "exact_name_matches", "header_name_rows", "filings_pre_first_observed_year"]:
        if c not in summary:
            summary[c] = 0
        summary[c] = summary[c].fillna(0).astype(int)
    summary.to_csv(a.out/"nsar_series_coverage.csv", index=False)
    annual = []
    for year in range(MIN_YEAR, MAX_YEAR+1):
        at_risk = summary[pd.to_numeric(summary.first_observed_year, errors="coerce").le(year)]
        prior = matches[pd.to_datetime(matches.filing_date, errors="coerce").dt.year.lt(year)] if not matches.empty else pd.DataFrame()
        prior_ids = set(prior.series_id.astype(str)) if not prior.empty else set()
        covered = len(prior_ids.intersection(set(at_risk.series_id.astype(str))))
        annual.append({"observation_year": year, "target_series_observed_by_year": len(at_risk),
                       "target_series_with_NSAR_header_filed_before_year": covered,
                       "coverage_pct": round(100*covered/len(at_risk), 2) if len(at_risk) else None})
    pd.DataFrame(annual).to_csv(a.out/"nsar_annual_prior_header_coverage.csv", index=False)
    target_ids = set(targets.series_id.astype(str))
    found_ids = set(matches.series_id.astype(str)) if not matches.empty else set()
    metrics = {
        "source": "SEC EDGAR public N-SAR submissions and actual submission headers",
        "sample_method": "same deterministic 80-CIK subset as prior SEC pilot; not probability-representative",
        "sampled_CIKs": len(sampled), "sampled_target_series": len(targets),
        "completed_CIKs": completed, "history_error_CIKs": int(sum(x["status"] == "history_error" for x in cik_rows)),
        "unprocessed_CIKs": len(sampled) - len(cik_rows),
        "target_series_found_in_any_NSAR_header": len(target_ids.intersection(found_ids)),
        "target_series_header_match_pct": round(100*len(target_ids.intersection(found_ids))/len(target_ids), 2) if target_ids else None,
        "registrants_with_at_least_one_NSAR_filing": int(filings.cik.nunique()) if not filings.empty else 0,
        "registrants_with_target_series_header_match": int(matches.cik.nunique()) if not matches.empty else 0,
        "selected_NSAR_filings": len(filings),
        "filing_status_counts": filings.status.value_counts(dropna=False).to_dict() if not filings.empty else {},
        "filing_forms": sorted(filings.form.dropna().unique().tolist()) if not filings.empty else [],
        "filing_year_min": int(pd.to_datetime(filings.filing_date, errors="coerce").dt.year.min()) if not filings.empty and pd.to_datetime(filings.filing_date, errors="coerce").notna().any() else None,
        "filing_year_max": int(pd.to_datetime(filings.filing_date, errors="coerce").dt.year.max()) if not filings.empty and pd.to_datetime(filings.filing_date, errors="coerce").notna().any() else None,
        "series_name_exact_matches": int(matches.series_name_exact_match.sum()) if not matches.empty else 0,
        "series_name_nonempty_header_rows": int(matches.historical_header_series_name.astype(str).str.len().gt(0).sum()) if not matches.empty else 0,
        "matches_with_class_ids": int(matches.header_class_count.gt(0).sum()) if not matches.empty else 0,
        "matches_filed_before_first_observed_year": int(matches.filing_precedes_first_observed_year.sum()) if not matches.empty else 0,
        "submission_header_errors": len(errors),
        "runtime_minutes": round((time.monotonic()-started)/60, 2),
        "runtime_deadline_minutes": a.max_runtime_minutes,
        "runtime_deadline_reached": bool(timed_out or time.monotonic() >= DEADLINE),
        "max_filings_per_CIK_year": 1, "strategy_labels_created": 0,
        "interpretation": "N-SAR header identifiers are identity evidence only. No strategy labels are created. This deterministic sample is not extrapolated to all 551 CIKs; one filing per CIK-year makes coverage a lower-bound probe."
    }
    (a.out/"nsar_linkage_metrics.json").write_text(json.dumps(metrics, indent=2, default=str)+"\n")
    report = ["# Historical N-SAR Series/Class Linkage Feasibility Audit", "",
        "**Identity audit only. No active/passive classifications are created.**", "",
        "## Results", "", json.dumps(metrics, indent=2, default=str), "",
        "The sample is the deterministic 80-CIK subset from the prior SEC coverage pilot, not a probability sample. One N-SAR filing per CIK-year is selected, preferring NSAR-B, over 1994–2018. Header matches are lower-bound identity evidence, not strategy evidence. Missing series IDs do not imply a fund did not exist or was passive.", "",
        "## Outputs", "",
        "- nsar_filing_headers.csv — selected N-SAR filing diagnostics.",
        "- nsar_target_series_matches.csv — target series IDs found in actual headers, with names and classes.",
        "- nsar_series_coverage.csv — series-level linkage coverage.",
        "- nsar_annual_prior_header_coverage.csv — prior-filing identity coverage by observation year.",
        "- nsar_linkage_metrics.json — machine-readable results.",
        "- nsar_cik_processing_manifest.csv — explicit per-CIK completion and selected-filing counts.",
        "- nsar_api_errors.csv — bounded request errors.", ""]
    (a.out/"NSAR_SERIES_LINKAGE_FEASIBILITY_AUDIT.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(metrics, indent=2, default=str))


if __name__ == "__main__":
    main()
