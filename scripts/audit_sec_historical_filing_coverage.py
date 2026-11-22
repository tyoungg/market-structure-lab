#!/usr/bin/env python3
"""Historical SEC prospectus coverage audit for Petajisto-to-SEC matched series.

This is a bounded, reproducible lower-bound census. It scans up to N relevant
prospectus filings per registrant/calendar year, confirms series IDs in the
actual EDGAR submission header, and retrieves the primary prospectus document
only when it names a matched series. Registry matches alone are never counted
as historical filing or strategy evidence.
"""
import argparse
import html
import json
import os
import re
import time
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

FORMS = {"485BPOS", "485APOS", "485BXT", "N-1A", "497K", "497"}
PRIORITY = {"485BPOS": 0, "485APOS": 1, "N-1A": 2, "485BXT": 3, "497K": 4, "497": 5}
MIN_YEAR, MAX_YEAR = 1994, 2009
DELAY = 0.12
MAX_PREFIX = 1_048_576
DEADLINE = None


def session():
    email = os.environ.get("SEC_CONTACT_EMAIL", "").strip()
    if not email:
        raise RuntimeError("SEC_CONTACT_EMAIL environment variable is required")
    s = requests.Session()
    retry = Retry(total=2, connect=2, read=2, status=2, backoff_factor=0.5,
                  status_forcelist=[408, 429, 500, 502, 503, 504],
                  allowed_methods=frozenset(["GET"]), respect_retry_after_header=False,
                  raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=8)
    s.mount("https://", adapter)
    s.headers.update({
        "User-Agent": "The Rational Coward Research Project (tyoungg/market-structure-lab; contact " + email + ")",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })
    return s


def get(s, url, **kwargs):
    if DEADLINE is not None and time.monotonic() >= DEADLINE:
        raise TimeoutError("historical SEC audit reached its runtime deadline")
    time.sleep(DELAY)
    response = s.get(url, timeout=(10, 30), **kwargs)
    response.raise_for_status()
    if DEADLINE is not None and time.monotonic() >= DEADLINE:
        response.close()
        raise TimeoutError("historical SEC audit reached its runtime deadline")
    return response


def get_json(s, url):
    return get(s, url).json()


def load_history(s, cik):
    root = f"https://data.sec.gov/submissions/CIK{str(cik).zfill(10)}.json"
    payload = get_json(s, root)
    frames = []
    recent = pd.DataFrame(payload.get("filings", {}).get("recent", {}))
    if not recent.empty:
        frames.append(recent)
    for item in payload.get("filings", {}).get("files", []) or []:
        start = pd.to_datetime(item.get("filingFrom"), errors="coerce")
        end = pd.to_datetime(item.get("filingTo"), errors="coerce")
        if pd.isna(start) or pd.isna(end) or end.year < MIN_YEAR or start.year > MAX_YEAR:
            continue
        name = item.get("name")
        if name:
            frame = pd.DataFrame(get_json(s, "https://data.sec.gov/submissions/" + name))
            if not frame.empty:
                frames.append(frame)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True, sort=False)
    if "accessionNumber" in out:
        out = out.drop_duplicates("accessionNumber", keep="first")
    return out


def submission_prefix(s, cik, accession):
    acc = str(accession).replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{accession}.txt"
    response = get(s, url, headers={"Range": f"bytes=0-{MAX_PREFIX - 1}"}, stream=True)
    parts, size = [], 0
    try:
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            take = min(len(chunk), MAX_PREFIX - size)
            parts.append(chunk[:take])
            size += take
            if size >= MAX_PREFIX:
                break
    finally:
        response.close()
    text = b"".join(parts).decode("utf-8", errors="replace")
    if len(text) < 1000:
        raise ValueError(f"submission prefix unexpectedly short ({len(text)} chars)")
    ids = sorted(set(re.findall(r"\bS\d{9}\b", text)))
    return text, ids, url


def primary_filename(submission, form):
    blocks = re.split(r"(?i)<DOCUMENT>", submission)[1:]
    candidates = []
    for block in blocks:
        header = re.split(r"(?i)<TEXT>", block, maxsplit=1)[0][:10000]
        typ = re.search(r"(?im)^\s*<TYPE>\s*([^\r\n<]+)", header)
        seq = re.search(r"(?im)^\s*<SEQUENCE>\s*(\d+)", header)
        filename = re.search(r"(?im)^\s*<FILENAME>\s*([^\r\n<]+)", header)
        if typ and filename and typ.group(1).strip().upper() == str(form).upper():
            candidates.append((int(seq.group(1)) if seq else 999999, filename.group(1).strip()))
    if not candidates:
        raise ValueError(f"no primary document header for form {form}")
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][1].rsplit("/", 1)[-1]


def download_primary(s, cik, accession, submission, form):
    acc = str(accession).replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/"
    filename = primary_filename(submission, form)
    index = get_json(s, base + "index.json")
    items = index.get("directory", {}).get("item", [])
    if not any(str(x.get("name", "")) == filename for x in items):
        raise ValueError(f"primary document {filename} absent from filing index")
    url = base + filename
    raw = get(s, url).text
    if len(raw) < 1000:
        raise ValueError(f"primary document unexpectedly short ({len(raw)} chars)")
    raw = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", raw)
    plain = html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))
    plain = re.sub(r"\s+", " ", plain)
    if len(plain) < 1000:
        raise ValueError("primary document text extraction unexpectedly short")
    return url, plain


def normalize(s):
    x = str(s or "").upper().replace("&", " AND ")
    x = re.sub(r"\b(CLASS|SHARES?|FUND|FUNDS|PORTFOLIO|SERIES)\b", " ", x)
    return " ".join(re.findall(r"[A-Z0-9]+", x))


def series_context(text, series_name, sibling_names, radius=5000):
    if not series_name or len(normalize(series_name).replace(" ", "")) < 8:
        return []
    name_pat = re.compile(re.escape(str(series_name)), re.IGNORECASE)
    heading_pat = re.compile(r"\b(?:principal\s+)?investment\s+strateg(?:y|ies)\b", re.IGNORECASE)
    end_pat = re.compile(
        r"\b(?:principal\s+investment\s+risks?|portfolio\s+holdings|management\s+of\s+the\s+fund|"
        r"fund\s+management|purchase\s+and\s+sale\s+of\s+fund\s+shares|additional\s+information)\b",
        re.IGNORECASE)
    sibling_hits = []
    for sibling in sibling_names:
        if sibling and str(sibling).casefold() != str(series_name).casefold():
            sibling_hits.extend(m.start() for m in re.finditer(re.escape(str(sibling)), text, re.IGNORECASE))
    sibling_hits.sort()
    chunks = []
    for match in name_pat.finditer(text):
        pos = match.start()
        next_sibling = next((x for x in sibling_hits if x > pos), len(text))
        boundary = min(len(text), pos + radius, next_sibling)
        heading = heading_pat.search(text, pos, boundary)
        if not heading:
            continue
        end = end_pat.search(text, heading.end(), min(len(text), heading.end() + radius, next_sibling))
        stop = end.start() if end else min(len(text), heading.end() + radius, next_sibling)
        chunk = text[heading.start():stop].strip()
        if len(chunk) > 100:
            chunks.append(chunk[:radius])
    return list(dict.fromkeys(chunks))[:5]


def classify(text):
    t = re.sub(r"\s+", " ", text.lower())
    patterns = {
        "enhanced index": [r"enhanced[\s-]+index(?:ing)?", r"index[\s-]+enhancement"],
        "index": [r"\bis an index fund\b", r"\bseeks? to track (?:the )?(?:investment results|performance)",
                  r"\bfull replication strategy\b", r"replicate the performance of",
                  r"correspond generally to the performance of"],
        "active": [r"\bis actively managed\b", r"\bactively manages\b", r"\bactive stock selection\b",
                   r"\bactive management strategy\b", r"does not seek to track", r"is not an index fund",
                   r"\b(?:team|portfolio managers?|investment managers?|fmr)\s+(?:ranks?|selects?|chooses?|identifies?)\s+(?:the\s+)?(?:individual\s+)?(?:stocks|securities|companies)\b",
                   r"\b(?:subjects?|evaluates?|analyzes?)\s+(?:the\s+)?(?:most\s+)?(?:attractively\s+)?(?:ranked\s+)?(?:stocks|securities)\b",
                   r"\b(?:actively managed|discretionary|fundamental(?:ly)? based)\s+(?:stock|security) selection\b",
                   r"\b(?:uses?|employs?|follows?)\s+(?:a\s+)?(?:fundamental(?:ly)? based\s+)?(?:stock|security) selection (?:process|approach)\b",
                   r"\b(?:fmr|the adviser|the investment team|the portfolio management team)\s+(?:invests|selects|chooses)\b.{0,180}\b(?:believes|considers|determines)\b"],
    }
    found = {k: [m.group(0) for p in pats for m in re.finditer(p, t)] for k, pats in patterns.items()}
    present = [k for k, v in found.items() if v]
    if "enhanced index" in present:
        label = "enhanced index"
    elif "index" in present and "active" not in present:
        label = "index"
    elif "active" in present and "index" not in present:
        label = "active"
    else:
        label = "unclassified"
    phrases = " | ".join(f"{k}:{v}" for k, vals in found.items() for v in vals[:3])
    return label, phrases


def choose_filings(history, max_per_year):
    if history.empty or not {"filingDate", "form", "accessionNumber"}.issubset(history.columns):
        return pd.DataFrame(), 0
    df = history.copy()
    df["filingDate"] = pd.to_datetime(df["filingDate"], errors="coerce")
    df["form"] = df["form"].astype(str).str.upper()
    df = df[df.form.isin(FORMS) & df.filingDate.dt.year.between(MIN_YEAR, MAX_YEAR)].copy()
    if df.empty:
        return df, 0
    df["year"] = df.filingDate.dt.year
    df["priority"] = df.form.map(PRIORITY).fillna(99)
    selected, cap_hits = [], 0
    for year, group in df.groupby("year"):
        group = group.sort_values(["priority", "filingDate", "accessionNumber"],
                                  ascending=[True, False, True])
        if len(group) > max_per_year:
            cap_hits += 1
        selected.append(group.head(max_per_year))
    return pd.concat(selected, ignore_index=True), cap_hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fund-period-csv", required=True, type=Path)
    ap.add_argument("--fund-year-csv", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--max-filings-per-cik-year", type=int, default=1)
    ap.add_argument("--max-filings-per-cik", type=int, default=4)
    ap.add_argument("--max-ciks", type=int, default=80)
    ap.add_argument("--max-runtime-minutes", type=int, default=70)
    a = ap.parse_args()
    if min(a.max_filings_per_cik_year, a.max_filings_per_cik, a.max_ciks, a.max_runtime_minutes) < 1:
        raise ValueError("All runtime and sampling limits must be positive")
    global DEADLINE
    started = time.monotonic()
    DEADLINE = started + a.max_runtime_minutes * 60
    a.out.mkdir(parents=True, exist_ok=True)

    period = pd.read_csv(a.fund_period_csv, dtype=str, low_memory=False)
    year = pd.read_csv(a.fund_year_csv, dtype=str, low_memory=False)
    required = {"fundno_key", "year", "series_match_status", "matched_series_id"}
    if not required.issubset(year.columns):
        raise ValueError(f"fund-year input missing columns: {sorted(required - set(year.columns))}")
    targets = period[period.series_match_status.eq("unique_series")].copy()
    targets = targets.dropna(subset=["matched_cik", "matched_series_id"])
    targets["matched_cik"] = targets.matched_cik.astype(str).str.zfill(10)
    targets["matched_series_id"] = targets.matched_series_id.astype(str)
    series = (targets.groupby(["matched_cik", "matched_series_id"])
              .agg(series_name=("matched_series_name", "first"),
                   first_observed_year=("year", "min"), last_observed_year=("year", "max"),
                   observed_fundnos=("fundno_key", lambda x: "|".join(sorted(set(x)))))
              .reset_index())
    all_series_by_cik = {cik: g.to_dict("records") for cik, g in series.groupby("matched_cik")}
    cik_summary = (series.groupby("matched_cik").agg(
        series_count=("matched_series_id", "nunique"),
        first_observed_year=("first_observed_year", "min"),
        last_observed_year=("last_observed_year", "max")).reset_index()
        .sort_values(["first_observed_year", "series_count", "matched_cik"]).reset_index(drop=True))
    all_ciks = len(cik_summary)
    if all_ciks > a.max_ciks:
        # Deterministic systematic sample across the sorted time/registrant-size distribution.
        indices = sorted({round(i * (all_ciks - 1) / max(a.max_ciks - 1, 1))
                          for i in range(a.max_ciks)})
        selected_ciks = set(cik_summary.iloc[indices].matched_cik.astype(str))
    else:
        selected_ciks = set(cik_summary.matched_cik.astype(str))
    series_by_cik = {cik: all_series_by_cik[cik] for cik in sorted(selected_ciks)}
    names_by_cik = {cik: [str(x["series_name"]) for x in rows] for cik, rows in series_by_cik.items()}
    s = session()
    candidate_rows, evidence_rows, api_errors = [], [], []
    total_cap_hits = 0
    completed_ciks = 0
    timed_out = False
    max_total_filings = a.max_ciks * a.max_filings_per_cik

    for cik_number, (cik, target_rows) in enumerate(series_by_cik.items(), start=1):
        if time.monotonic() >= DEADLINE:
            timed_out = True
            break
        print(f"[{cik_number}/{len(series_by_cik)}] Scanning CIK {cik}", flush=True)
        try:
            history = load_history(s, cik)
        except Exception as exc:
            api_errors.append({"cik": cik, "error": f"{type(exc).__name__}:{exc}"})
            continue
        filings, cap_hits = choose_filings(history, a.max_filings_per_cik_year)
        total_cap_hits += cap_hits
        if len(filings) > a.max_filings_per_cik:
            positions = sorted({round(i * (len(filings) - 1) / max(a.max_filings_per_cik - 1, 1))
                                for i in range(a.max_filings_per_cik)})
            filings = filings.iloc[positions].copy()
        remaining = max_total_filings - len(candidate_rows)
        filings = filings.head(max(0, remaining))
        print(f"  selected {len(filings)} bounded candidates; capped years={cap_hits}", flush=True)
        target_ids = {str(x["matched_series_id"]) for x in target_rows}
        names = {str(x["matched_series_id"]): str(x["series_name"]) for x in target_rows}
        for filing in filings.to_dict("records"):
            if time.monotonic() >= DEADLINE or len(candidate_rows) >= max_total_filings:
                timed_out = time.monotonic() >= DEADLINE
                break
            accession = str(filing.get("accessionNumber", ""))
            form = str(filing.get("form", "")).upper()
            filing_date = pd.to_datetime(filing.get("filingDate"), errors="coerce")
            base = {"cik": cik, "accession": accession, "form": form,
                    "filing_date": str(filing_date.date()) if pd.notna(filing_date) else "",
                    "filing_year": int(filing_date.year) if pd.notna(filing_date) else None,
                    "series_ids_in_submission": 0, "matched_series_count": 0,
                    "matched_series_ids": "", "primary_document_url": "",
                    "status": "", "detail": ""}
            try:
                submission, ids, _ = submission_prefix(s, cik, accession)
                matched_ids = sorted(target_ids.intersection(ids))
                base["series_ids_in_submission"] = len(ids)
                base["matched_series_count"] = len(matched_ids)
                base["matched_series_ids"] = "|".join(matched_ids)
                if not matched_ids:
                    base["status"] = "submission_accessible_no_matched_series_id"
                    candidate_rows.append(base)
                    continue
                try:
                    doc_url, doc_text = download_primary(s, cik, accession, submission, form)
                    base["primary_document_url"] = doc_url
                    base["status"] = "prospectus_document_accessible"
                    for sid in matched_ids:
                        chunks = series_context(doc_text, names.get(sid, ""), names_by_cik[cik])
                        context = " ".join(chunks)
                        label, phrases = classify(context) if context else ("unclassified", "")
                        evidence_rows.append({
                            "cik": cik, "series_id": sid, "series_name": names.get(sid, ""),
                            "filing_date": base["filing_date"], "form": form, "accession": accession,
                            "filing_url": doc_url, "prospectus_accessible": True,
                            "strategy_context_found": bool(context), "classification": label,
                            "evidence_phrases": phrases,
                            "evidence_context": context[:2000],
                        })
                except Exception as exc:
                    base["status"] = "series_confirmed_document_error"
                    base["detail"] = f"{type(exc).__name__}:{exc}"
                    for sid in matched_ids:
                        evidence_rows.append({
                            "cik": cik, "series_id": sid, "series_name": names.get(sid, ""),
                            "filing_date": base["filing_date"], "form": form, "accession": accession,
                            "filing_url": "", "prospectus_accessible": False,
                            "strategy_context_found": False, "classification": "unclassified",
                            "evidence_phrases": "DOCUMENT_RETRIEVAL_ERROR",
                            "evidence_context": "",
                        })
            except Exception as exc:
                base["status"] = "submission_header_error"
                base["detail"] = f"{type(exc).__name__}:{exc}"
            candidate_rows.append(base)
        completed_ciks += 1
        # Persist a checkpoint after every registrant so interrupted runs retain completed work.
        pd.DataFrame(candidate_rows).to_csv(a.out / "sec_historical_filing_candidates_checkpoint.csv", index=False)
        pd.DataFrame(evidence_rows).to_csv(a.out / "sec_historical_series_filing_evidence_checkpoint.csv", index=False)
        if timed_out or len(candidate_rows) >= max_total_filings:
            break

    candidates = pd.DataFrame(candidate_rows)
    evidence = pd.DataFrame(evidence_rows)
    if candidates.empty:
        candidates = pd.DataFrame(columns=["cik", "accession", "form", "filing_date", "filing_year",
                                           "series_ids_in_submission", "matched_series_count",
                                           "matched_series_ids", "primary_document_url", "status", "detail"])
    if evidence.empty:
        evidence = pd.DataFrame(columns=["cik", "series_id", "series_name", "filing_date", "form",
                                         "accession", "filing_url", "prospectus_accessible",
                                         "strategy_context_found", "classification", "evidence_phrases",
                                         "evidence_context"])
    candidates.to_csv(a.out / "sec_historical_filing_candidates.csv", index=False)
    evidence.to_csv(a.out / "sec_historical_series_filing_evidence.csv", index=False)
    pd.DataFrame(api_errors).to_csv(a.out / "sec_historical_submission_api_errors.csv", index=False)

    # Resolve one stable CIK/name for each unique fund-year series match.
    map_rows = (targets.groupby(["fundno_key", "year", "matched_series_id"])
                .agg(matched_cik=("matched_cik", lambda x: next(iter(set(x))) if len(set(x)) == 1 else ""),
                     matched_series_name=("matched_series_name", "first"))
                .reset_index())
    map_rows["year"] = map_rows.year.astype(str)
    year = year.merge(map_rows, on=["fundno_key", "year", "matched_series_id"], how="left")
    evidence["filing_date_parsed"] = pd.to_datetime(evidence.filing_date, errors="coerce")
    evidence["prospectus_accessible"] = evidence.prospectus_accessible.astype(str).str.lower().eq("true")
    coverage_rows = []
    for row in year.to_dict("records"):
        yr = int(row["year"])
        sid = str(row.get("matched_series_id") or "")
        cik = str(row.get("matched_cik") or "")
        unique = row.get("series_match_status") == "unique_series" and sid not in {"", "nan"}
        if not unique:
            coverage_rows.append({**row, "coverage_status": "no_unique_2010_registry_series_match",
                                  "prior_series_filings": 0, "prior_accessible_prospectuses": 0,
                                  "prior_strategy_evidence_filings": 0, "latest_prior_prospectus_date": "",
                                  "strategy_class_asof": "unclassified"})
            continue
        if not cik or cik == "nan":
            prior = evidence.iloc[0:0]
            status = "unique_registry_match_missing_cik_mapping"
        elif cik not in selected_ciks:
            prior = evidence.iloc[0:0]
            status = "cik_not_in_historical_sample"
        elif yr <= MIN_YEAR:
            prior = evidence.iloc[0:0]
            status = "pre_edgar_electronic_archive"
        else:
            cutoff = pd.Timestamp(year=yr, month=1, day=1)
            prior = evidence[(evidence.series_id.eq(sid)) &
                             (evidence.cik.eq(cik)) &
                             (evidence.filing_date_parsed < cutoff)].copy()
            confirmed = len(prior)
            accessible = prior[prior.prospectus_accessible]
            status = ("strategy_evidence_before_year" if
                      (accessible.classification.isin(["active", "index", "enhanced index"]).any()) else
                      ("accessible_prospectus_before_year" if len(accessible) else
                       ("series_in_filing_header_before_year" if confirmed else
                        "no_prior_series_specific_filing_found")))
        accessible = prior[prior.prospectus_accessible]
        labels = set(accessible.loc[accessible.classification.isin(
            ["active", "index", "enhanced index"]), "classification"].astype(str))
        strategy = next(iter(labels)) if len(labels) == 1 else "unclassified"
        latest = accessible.filing_date_parsed.max() if len(accessible) else pd.NaT
        coverage_rows.append({
            **row, "coverage_status": status, "prior_series_filings": len(prior),
            "prior_accessible_prospectuses": len(accessible),
            "prior_strategy_evidence_filings": int(accessible.classification.isin(
                ["active", "index", "enhanced index"]).sum()),
            "latest_prior_prospectus_date": str(latest.date()) if pd.notna(latest) else "",
            "strategy_class_asof": strategy if len(labels) == 1 else "unclassified",
            "strategy_class_conflict_asof": len(labels) > 1,
        })
    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(a.out / "sec_historical_coverage_by_fund_year.csv", index=False)

    annual = (coverage.groupby("year").agg(
        fund_year_rows=("fundno_key", "size"),
        unique_2010_registry_series_matches=("series_match_status", lambda x: int(x.eq("unique_series").sum())),
        series_confirmed_before_year=("coverage_status", lambda x: int(x.isin([
            "series_in_filing_header_before_year", "accessible_prospectus_before_year",
            "strategy_evidence_before_year"]).sum())),
        accessible_prospectus_before_year=("coverage_status", lambda x: int(x.isin([
            "accessible_prospectus_before_year", "strategy_evidence_before_year"]).sum())),
        strategy_evidence_before_year=("coverage_status", lambda x: int(x.eq("strategy_evidence_before_year").sum())),
        pre_edgar_fund_years=("coverage_status", lambda x: int(x.eq("pre_edgar_electronic_archive").sum())),
        no_prior_series_specific_filing=("coverage_status", lambda x: int(x.eq("no_prior_series_specific_filing_found").sum())),
        not_scanned_cik_sample=("coverage_status", lambda x: int(x.eq("cik_not_in_historical_sample").sum()))
    ).reset_index())
    for col in ["series_confirmed_before_year", "accessible_prospectus_before_year",
                "strategy_evidence_before_year"]:
        denom = annual.unique_2010_registry_series_matches.replace(0, pd.NA)
        annual[col + "_pct_of_registry_matches"] = (100 * annual[col] / denom).round(2)
    annual.to_csv(a.out / "sec_historical_coverage_by_year.csv", index=False)

    series_cov = series.rename(columns={
        "matched_cik": "cik", "matched_series_id": "series_id"
    }).copy()
    if not evidence.empty:
        evidence_summary = evidence.groupby(["cik", "series_id"]).agg(
            filings_identifying_series=("accession", "nunique"),
            accessible_prospectus_filings=("prospectus_accessible", "sum"),
            strategy_context_filings=("strategy_context_found", "sum"),
            explicit_classifications=("classification", lambda x: int(x.isin(
                ["active", "index", "enhanced index"]).sum())),
            first_filing_date=("filing_date", "min"),
            last_filing_date=("filing_date", "max"),
        ).reset_index()
        series_cov = series_cov.merge(evidence_summary, on=["cik", "series_id"], how="left")
    else:
        for col in ["filings_identifying_series", "accessible_prospectus_filings",
                    "strategy_context_filings", "explicit_classifications"]:
            series_cov[col] = 0
        series_cov["first_filing_date"] = ""
        series_cov["last_filing_date"] = ""
    for col in ["filings_identifying_series", "accessible_prospectus_filings",
                "strategy_context_filings", "explicit_classifications"]:
        series_cov[col] = series_cov[col].fillna(0).astype(int)
    series_cov.to_csv(a.out / "sec_historical_coverage_by_series.csv", index=False)

    metrics = {
        "scope": "All CIKs attached to unique-series matches in the Petajisto/TR panel",
        "unique_matched_ciks": int(series.matched_cik.nunique()),
        "sampled_ciks": len(selected_ciks),
        "ciks_not_sampled": int(max(0, all_ciks - len(selected_ciks))),
        "unique_matched_series": int(series.matched_series_id.nunique()),
        "series_in_sampled_ciks": int(series[series.matched_cik.isin(selected_ciks)].matched_series_id.nunique()),
        "cik_sample_method": "deterministic systematic sample sorted by first observed year, series count, and CIK",
        "max_filings_per_cik": int(a.max_filings_per_cik),
        "max_total_filing_candidates": int(max_total_filings),
        "completed_ciks": int(completed_ciks),
        "runtime_minutes": round((time.monotonic() - started) / 60, 2),
        "runtime_deadline_minutes": int(a.max_runtime_minutes),
        "runtime_deadline_reached": bool(timed_out or time.monotonic() >= DEADLINE),
        "matched_series_fund_year_rows": int((year.series_match_status == "unique_series").sum()),
        "filing_forms_scanned": sorted(FORMS),
        "edgar_electronic_archive_start_year": MIN_YEAR,
        "edgar_electronic_archive_end_year": MAX_YEAR,
        "max_filings_per_cik_year": int(a.max_filings_per_cik_year),
        "cik_years_hit_filing_cap": int(total_cap_hits),
        "submission_api_error_ciks": len(api_errors),
        "selected_filing_candidates": len(candidates),
        "candidate_status_counts": candidates.status.value_counts(dropna=False).to_dict(),
        "series_filing_evidence_rows": len(evidence),
        "series_confirmed_in_submission_headers": int(evidence.series_id.nunique()) if not evidence.empty else 0,
        "series_with_accessible_prospectus": int(evidence.loc[evidence.prospectus_accessible, "series_id"].nunique()) if not evidence.empty else 0,
        "series_with_explicit_strategy_evidence": int(evidence.loc[
            evidence.classification.isin(["active", "index", "enhanced index"]), "series_id"].nunique()) if not evidence.empty else 0,
        "filing_strategy_classification_counts": evidence.classification.value_counts(dropna=False).to_dict() if not evidence.empty else {},
        "annual_coverage": annual.to_dict("records"),
        "interpretation": "Registry matches are not historical evidence. Series IDs in actual filing headers establish series-specific filing linkage; successful primary-document retrieval establishes accessible prospectus evidence; only explicit fund-specific text supports a strategy label. Coverage is a lower bound because the scan is capped at the configured number of filings per CIK-year.",
    }
    (a.out / "sec_historical_coverage_metrics.json").write_text(
        json.dumps(metrics, indent=2, default=str), encoding="utf-8")
    report = [
        "# Historical SEC Prospectus Coverage Audit", "",
        "## Scope and method",
        f"- Matched registrants in full bridge: {metrics['unique_matched_ciks']:,}; sampled registrants: {metrics['sampled_ciks']:,}; not sampled: {metrics['ciks_not_sampled']:,}.",
        f"- Matched series in full bridge: {metrics['unique_matched_series']:,}; series represented in sampled registrants: {metrics['series_in_sampled_ciks']:,}.",
        f"- Completed registrants: {metrics['completed_ciks']:,}; runtime: {metrics['runtime_minutes']} minutes; deadline reached: {metrics['runtime_deadline_reached']}.",
        f"- Candidate forms: {', '.join(sorted(FORMS))}.",
        f"- Electronic EDGAR window scanned: {MIN_YEAR}–{MAX_YEAR}; pre-1994 years are reported separately.",
        f"- Filing limits: at most {a.max_filings_per_cik_year} per registrant/year and {a.max_filings_per_cik} per registrant; global candidate ceiling {max_total_filings:,}.",
        f"- Registrant sample: deterministic systematic sample of {len(selected_ciks):,} from {all_ciks:,} matched registrants; not a census.",
        "- A filing counts as series-confirmed only when the matched SEC series ID appears in the actual submission header.",
        "- A prospectus counts as accessible only when its primary document is successfully retrieved and text-extracted.",
        "- Strategy labels require explicit fund-specific prospectus text. Missing text is unclassified, not active.", "",
        "## Annual coverage", "", annual.to_markdown(index=False), "",
        "## Key totals",
        f"- Selected filing candidates: {len(candidates):,}.",
        f"- Series-specific filing evidence rows: {len(evidence):,}.",
        f"- Matched series with accessible prospectus: {metrics['series_with_accessible_prospectus']:,}.",
        f"- Matched series with explicit strategy evidence: {metrics['series_with_explicit_strategy_evidence']:,}.",
        f"- SEC submissions API errors: {len(api_errors):,}.", "",
        "## Interpretation limits",
        "This is a bounded, sampled lower-bound coverage audit, not a complete EDGAR census. Only a deterministic systematic sample of registrants is scanned, with per-year, per-registrant, global candidate, and runtime ceilings. Unselected registrants are explicitly labeled not sampled, not as having no filings. A CIK-level filing without the matched series ID is not treated as evidence for that fund. A series ID in a submission header confirms filing linkage but not strategy. An accessible prospectus without an extracted fund-specific strategy section remains unclassified. EDGAR's electronic archive begins in 1994; absence of electronic filings before that date says nothing about paper prospectuses or historical fund status. The 2010 registry snapshot remains a candidate-linkage source, not proof of historical registration.", "",
        "## Output inventory",
        "- sec_historical_filing_candidates.csv",
        "- sec_historical_series_filing_evidence.csv",
        "- sec_historical_coverage_by_fund_year.csv",
        "- sec_historical_coverage_by_year.csv",
        "- sec_historical_coverage_by_series.csv",
        "- sec_historical_submission_api_errors.csv",
        "- sec_historical_coverage_metrics.json",
    ]
    (a.out / "SEC_HISTORICAL_FILING_COVERAGE_AUDIT.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2, default=str))


if __name__ == "__main__":
    main()
