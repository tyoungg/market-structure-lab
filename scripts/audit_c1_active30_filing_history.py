#!/usr/bin/env python3
"""Independent, targeted EDGAR filing-history audit for the 30 C.1 active fund-years.

This audit does not re-adjudicate strategy automatically. It exhaustively retrieves
relevant prospectus/SAI/supplement filings for the nine registrants represented in
the 30-row manual seed set, then links documents to the 14 target SEC series by
submission-header series IDs and fund-name aliases. Outputs are an auditable
candidate inventory for human review.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import os
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

FORMS = {"485APOS", "485BPOS", "485BXT", "N-1A", "N-1A/A", "497", "497K", "497J", "497AD", "497V"}
START_DATE = date(2005, 1, 1)
END_DATE = date(2008, 12, 31)
DELAY_SECONDS = 0.12
MAX_PREFIX_BYTES = 2 * 1024 * 1024
MAX_DOC_BYTES = 25 * 1024 * 1024

# Name variants are explicit, auditable aliases—not fuzzy identity matches.
ALIASES = {
    "S000000340": [
        "Dreyfus S&P STARS Fund",
        "Dreyfus Premier S&P STARS Fund",
    ],
    "S000000341": [
        "Dreyfus S&P STARS Opportunities Fund",
        "Dreyfus Premier S&P STARS Opportunities Fund",
    ],
    "S000000667": [
        "Legg Mason Capital Management Opportunity Trust",
        "Legg Mason Opportunity Trust",
    ],
    "S000000758": ["Baird LargeCap Fund"],
    "S000000759": ["Baird MidCap Fund"],
    "S000000760": ["Baird SmallCap Fund"],
    "S000001455": [
        "TOUCHSTONE SANDS CAPITAL INSTITUTIONAL GROWTH FUND",
        "CIP Sands Capital Institutional Growth Portfolio",
        "Sands Capital Institutional Growth Portfolio",
    ],
    "S000002365": [
        "Morgan Stanley Mid Cap Value Fund",
        "Morgan Stanley Mid-Cap Value Fund",
    ],
    "S000002422": ["OPTIMUM LARGE CAP GROWTH FUND"],
    "S000002424": [
        "OPTIMUM SMALL-MID CAP GROWTH FUND",
        "OPTIMUM SMALL CAP GROWTH FUND",
    ],
    "S000002425": [
        "OPTIMUM SMALL-MID CAP VALUE FUND",
        "OPTIMUM SMALL CAP VALUE FUND",
    ],
    "S000006164": ["Fort Pitt Capital Total Return Fund"],
    "S000010501": ["The Hillman Focused Advantage Fund", "Hillman Focused Advantage Fund"],
    "S000023592": ["Calvert Large Cap Value Fund"],
}

DATE_PATTERN = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4}\b",
    re.IGNORECASE,
)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%B %d %Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            pass
    return None


def date_string(value: date | None) -> str:
    return value.isoformat() if value else ""


def strict_asof(filing_date: date | None, cutoff: date) -> bool:
    return filing_date is not None and filing_date < cutoff


def classify_document(text: str, form: str, description: str = "") -> str:
    head = (text or "")[:5000].lower()
    hint = (description or "").lower()
    if "supplement to" in head or "supplement to" in hint or "important notice regarding change" in head:
        return "supplement"
    if "statement of additional information" in head[:2500] or "statement of additional information" in hint:
        return "sai"
    if "prospectus" in head[:3500] or form in {"497K"}:
        return "prospectus"
    if form in {"485APOS", "485BPOS", "485BXT", "N-1A"}:
        return "registration_amendment"
    return "other"


def extract_dates(text: str) -> tuple[str, str, str]:
    """Return prospectus-date candidates, supplement-date candidates, effective-date candidates."""
    t = text or ""
    prospectus_dates: list[str] = []
    for match in re.finditer(r"\bPROSPECTUS\b", t, re.IGNORECASE):
        window = t[match.end(): match.end() + 220]
        found = DATE_PATTERN.search(window)
        if found:
            prospectus_dates.append(found.group(0))
    supplement_dates = []
    for pattern in (
        r"(?:this|the) supplement is dated\s+(" + DATE_PATTERN.pattern + r")",
        r"supplement dated\s+(" + DATE_PATTERN.pattern + r")",
    ):
        supplement_dates.extend(m.group(1) for m in re.finditer(pattern, t, re.IGNORECASE))
    effective_dates = []
    effective_patterns = (
        r"will become effective.{0,180}?\bon\s+(" + DATE_PATTERN.pattern + r")",
        r"\bon\s+(" + DATE_PATTERN.pattern + r")\s+pursuant to paragraph",
        r"\beffective\s+(?:on|as of|at the close of business on)\s+(" + DATE_PATTERN.pattern + r")",
        r"\bbegin serving.{0,100}?\bon or about\s+(" + DATE_PATTERN.pattern + r")",
    )
    for pattern in effective_patterns:
        effective_dates.extend(m.group(1) for m in re.finditer(pattern, t, re.IGNORECASE | re.DOTALL))
    return (
        " | ".join(dict.fromkeys(prospectus_dates)),
        " | ".join(dict.fromkeys(supplement_dates)),
        " | ".join(dict.fromkeys(effective_dates)),
    )


def extract_series_ids_from_submission_header(text: str) -> set[str]:
    """Read series IDs only from SEC-HEADER, never from document body text."""
    header = re.split(r"(?i)<DOCUMENT>", text or "", maxsplit=1)[0]
    return set(re.findall(r"\bS\d{9}\b", header))


def extract_submission_header(text: str) -> list[dict[str, str]]:
    """Parse document headers from the SEC complete-submission prefix."""
    rows = []
    blocks = re.split(r"(?i)<DOCUMENT>", text or "")[1:]
    for block in blocks:
        header = re.split(r"(?i)<TEXT>", block, maxsplit=1)[0][:12000]
        def field(pattern: str) -> str:
            m = re.search(pattern, header, re.IGNORECASE | re.MULTILINE)
            return m.group(1).strip() if m else ""
        rows.append({
            "type": field(r"^\s*<TYPE>\s*([^\r\n<]+)"),
            "sequence": field(r"^\s*<SEQUENCE>\s*(\d+)"),
            "filename": field(r"^\s*<FILENAME>\s*([^\r\n<]+)"),
            "description": field(r"^\s*<DESCRIPTION>\s*([^\r\n<]+)"),
        })
    return [r for r in rows if r["filename"]]


def html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", raw or "")
    raw = re.sub(r"(?i)</(?:p|div|tr|li|h[1-6]|br|table)>", "\n", raw)
    raw = html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))
    return re.sub(r"[ \t\r\f\v]+", " ", re.sub(r"\n\s*\n+", "\n", raw)).strip()


def pdf_to_text(raw: bytes) -> str:
    if PdfReader is None:
        return ""
    try:
        reader = PdfReader(io.BytesIO(raw))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


def match_series(
    series_id: str,
    header_ids: set[str],
    text: str,
) -> tuple[bool, str, str]:
    header_match = series_id in header_ids
    matches = [a for a in ALIASES.get(series_id, []) if a.casefold() in (text or "").casefold()]
    name_match = bool(matches)
    if header_match and name_match:
        return True, "header_and_name", matches[0]
    if header_match:
        return True, "header_only", ""
    if name_match:
        return True, "name_alias", matches[0]
    return False, "", ""


def extract_context(text: str, aliases: Iterable[str]) -> str:
    t = text or ""
    for alias in aliases:
        m = re.search(re.escape(alias), t, re.IGNORECASE)
        if not m:
            continue
        start = max(0, m.start() - 300)
        end = min(len(t), m.end() + 3200)
        chunk = t[start:end]
        # Prefer the fund's strategy section if it is close to the fund heading.
        strategy = re.search(r"(?:principal\s+)?investment\s+strateg(?:y|ies)", chunk, re.IGNORECASE)
        if strategy:
            return chunk[strategy.start(): min(len(chunk), strategy.start() + 2800)]
        return chunk
    return ""


def build_session() -> requests.Session:
    email = os.environ.get("SEC_CONTACT_EMAIL", "").strip()
    if not email:
        raise RuntimeError("SEC_CONTACT_EMAIL repository secret is required by SEC fair-access policy.")
    session = requests.Session()
    retry = Retry(
        total=3, connect=3, read=3, status=3, backoff_factor=0.5,
        status_forcelist=[408, 429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]), raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=8)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": f"The Rational Coward Research Project (tyoungg/market-structure-lab; contact {email})",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })
    return session


def get(session: requests.Session, url: str, **kwargs) -> requests.Response:
    time.sleep(DELAY_SECONDS)
    response = session.get(url, timeout=(15, 60), **kwargs)
    response.raise_for_status()
    return response


def get_json(session: requests.Session, url: str) -> dict:
    return get(session, url).json()


def load_cik_filings(session: requests.Session, cik: str) -> list[dict]:
    root = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    payload = get_json(session, root)
    frames: list[dict] = []
    recent = payload.get("filings", {}).get("recent", {})
    if recent:
        keys = list(recent.keys())
        for i in range(len(recent.get("accessionNumber", []))):
            frames.append({k: recent.get(k, [""] * (i + 1))[i] for k in keys})
    for archive in payload.get("filings", {}).get("files", []) or []:
        start = parse_date(archive.get("filingFrom"))
        end = parse_date(archive.get("filingTo"))
        if not start or not end or end < START_DATE or start > END_DATE:
            continue
        name = archive.get("name")
        if name:
            historical = get_json(session, "https://data.sec.gov/submissions/" + quote(name))
            keys = list(historical.keys())
            for i in range(len(historical.get("accessionNumber", []))):
                frames.append({k: historical.get(k, [""] * (i + 1))[i] for k in keys})
    unique = {}
    for row in frames:
        accession = str(row.get("accessionNumber", "")).strip()
        filed = parse_date(str(row.get("filingDate", "")))
        form = str(row.get("form", "")).upper().strip()
        if accession and filed and START_DATE <= filed <= END_DATE and form in FORMS:
            unique[accession] = row
    return sorted(unique.values(), key=lambda r: (str(r.get("filingDate", "")), str(r.get("accessionNumber", ""))))


def submission_prefix(session: requests.Session, cik: str, accession: str) -> str:
    compact = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{compact}/{accession}.txt"
    response = get(session, url, headers={"Range": f"bytes=0-{MAX_PREFIX_BYTES - 1}"}, stream=True)
    parts, size = [], 0
    try:
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            take = min(len(chunk), MAX_PREFIX_BYTES - size)
            parts.append(chunk[:take])
            size += take
            if size >= MAX_PREFIX_BYTES:
                break
    finally:
        response.close()
    return b"".join(parts).decode("utf-8", errors="replace")


def download_doc(session: requests.Session, cik: str, accession: str, filename: str) -> tuple[str, str, str]:
    compact = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{compact}/{quote(filename)}"
    response = get(session, url, stream=True)
    parts, size = [], 0
    try:
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            size += len(chunk)
            if size > MAX_DOC_BYTES:
                raise ValueError(f"document exceeds {MAX_DOC_BYTES} byte audit limit: {filename}")
            parts.append(chunk)
    finally:
        response.close()
    raw = b"".join(parts)
    digest = hashlib.sha256(raw).hexdigest()
    if filename.lower().endswith(".pdf"):
        text = pdf_to_text(raw)
    else:
        text = html_to_text(raw.decode("utf-8", errors="replace"))
    return url, text, digest


def document_candidates(headers: list[dict[str, str]], primary_document: str, form: str) -> list[dict[str, str]]:
    out = []
    seen = set()
    for h in headers:
        filename = h.get("filename", "").strip()
        if not filename or filename in seen:
            continue
        description = h.get("description", "")
        dtype = h.get("type", "").upper()
        relevant = (
            filename == primary_document
            or dtype == form
            or any(k in (filename + " " + description).lower()
                   for k in ("prospectus", "statement of additional information", "sai", "supplement"))
        )
        if relevant:
            out.append(h)
            seen.add(filename)
    if primary_document and primary_document not in seen:
        out.insert(0, {"type": form, "sequence": "1", "filename": primary_document, "description": "primary document"})
    return out


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def run(manual_csv: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    with manual_csv.open(newline="", encoding="utf-8-sig") as f:
        manual = list(csv.DictReader(f))
    targets = [
        r for r in manual
        if r.get("evidence_kind") == "prospectus_fund_year"
        and str(r.get("panel_eligible", "")).strip().lower() in {"true", "1", "yes"}
        and r.get("adjudicated_strategy_class") == "other_active_style"
    ]
    if len(targets) != 30:
        raise ValueError(f"Expected exactly 30 adjudicated active fund-years; found {len(targets)}")
    series_rows: dict[tuple[str, str], dict] = {}
    for row in targets:
        cik = str(row.get("cik_norm", "")).zfill(10)
        sid = str(row.get("series_id_norm", "")).strip()
        if not cik or not sid:
            raise ValueError(f"Missing CIK or series ID in manual row: {row}")
        series_rows.setdefault((cik, sid), row)
    if len(series_rows) != 14:
        raise ValueError(f"Expected 14 distinct SEC series; found {len(series_rows)}")

    session = build_session()
    inventory: list[dict] = []
    errors: list[dict] = []
    scanned_filings = 0
    downloaded_documents = 0
    matched_document_keys = set()
    ciks_processed = 0

    for cik in sorted({k[0] for k in series_rows}):
        target_for_cik = {sid: row for (c, sid), row in series_rows.items() if c == cik}
        try:
            filings = load_cik_filings(session, cik)
            ciks_processed += 1
        except Exception as exc:
            errors.append({"cik": cik, "accession": "", "stage": "submissions_history",
                           "error": f"{type(exc).__name__}: {exc}"})
            continue
        for filing in filings:
            scanned_filings += 1
            accession = str(filing.get("accessionNumber", ""))
            form = str(filing.get("form", "")).upper()
            filed = parse_date(str(filing.get("filingDate", "")))
            primary = str(filing.get("primaryDocument", "")).strip()
            try:
                prefix = submission_prefix(session, cik, accession)
                header_ids = set(re.findall(r"\bS\d{9}\b", prefix))
                headers = extract_submission_header(prefix)
                docs = document_candidates(headers, primary, form)
                for doc in docs:
                    filename = doc.get("filename", "")
                    if not filename:
                        continue
                    try:
                        url, text, digest = download_doc(session, cik, accession, filename)
                    except Exception as exc:
                        errors.append({"cik": cik, "accession": accession, "stage": f"download:{filename}",
                                       "error": f"{type(exc).__name__}: {exc}"})
                        continue
                    downloaded_documents += 1
                    for sid, target in target_for_cik.items():
                        matched, method, matched_alias = match_series(sid, header_ids, text)
                        if not matched:
                            continue
                        key = (cik, accession, filename, sid)
                        if key in matched_document_keys:
                            continue
                        matched_document_keys.add(key)
                        kind = classify_document(text, form, doc.get("description", ""))
                        prospectus_dates, supplement_dates, effective_dates = extract_dates(text)
                        excerpt = extract_context(text, ALIASES.get(sid, []))
                        inventory.append({
                            "cik": cik,
                            "series_id": sid,
                            "series_name": target.get("series_name", ""),
                            "fundno": target.get("fundno_key", ""),
                            "form": form,
                            "document_type": doc.get("type", ""),
                            "document_description": doc.get("description", ""),
                            "filename": filename,
                            "document_kind": kind,
                            "accession": accession,
                            "filing_date": date_string(filed),
                            "prospectus_date_candidates": prospectus_dates,
                            "supplement_date_candidates": supplement_dates,
                            "effective_date_candidates": effective_dates,
                            "match_method": method,
                            "matched_name_alias": matched_alias,
                            "series_id_in_submission_header": sid in header_ids,
                            "source_url": url,
                            "source_sha256": digest,
                            "text_length": len(text),
                            "strategy_context_excerpt": excerpt[:3200],
                        })
            except Exception as exc:
                errors.append({"cik": cik, "accession": accession, "stage": "submission_or_parse",
                               "error": f"{type(exc).__name__}: {exc}"})

    # Expand each document to the target fund-years for which the filing was available.
    fund_year_docs = []
    for target in targets:
        cutoff = date(int(target["fund_year"]), 1, 1)
        for doc in inventory:
            if doc["cik"] != str(target["cik_norm"]).zfill(10) or doc["series_id"] != target["series_id_norm"]:
                continue
            filed = parse_date(doc["filing_date"])
            if strict_asof(filed, cutoff):
                fund_year_docs.append({
                    **doc,
                    "fund_year": target["fund_year"],
                    "asof_cutoff": cutoff.isoformat(),
                    "filing_age_days": (cutoff - filed).days if filed else "",
                    "original_adjudication_accession": target.get("accession", ""),
                    "original_adjudication_filing_date": target.get("filing_date", ""),
                })

    # Per-fund-year summary deliberately reports candidate inventory, not an automatic adjudication.
    summaries = []
    for target in targets:
        cutoff = date(int(target["fund_year"]), 1, 1)
        docs = [
            d for d in fund_year_docs
            if d["fundno"] == target["fundno_key"] and d["fund_year"] == target["fund_year"]
        ]
        docs.sort(key=lambda d: (d["filing_date"], d["accession"]), reverse=True)
        base = [d for d in docs if d["document_kind"] == "prospectus"]
        supplements = [d for d in docs if d["document_kind"] == "supplement"]
        base.sort(key=lambda d: (d["filing_date"], d["accession"]), reverse=True)
        supplements.sort(key=lambda d: (d["filing_date"], d["accession"]), reverse=True)
        latest = base[0] if base else (docs[0] if docs else {})
        latest_supp = supplements[0] if supplements else {}
        summaries.append({
            "fundno": target["fundno_key"],
            "fund_year": target["fund_year"],
            "series_name": target["series_name"],
            "cik": str(target["cik_norm"]).zfill(10),
            "series_id": target["series_id_norm"],
            "asof_cutoff": cutoff.isoformat(),
            "candidate_document_count": len(docs),
            "candidate_base_prospectus_count": len(base),
            "candidate_supplement_count": len(supplements),
            "latest_base_or_candidate_accession": latest.get("accession", ""),
            "latest_base_or_candidate_filing_date": latest.get("filing_date", ""),
            "latest_base_or_candidate_document_kind": latest.get("document_kind", ""),
            "latest_base_or_candidate_url": latest.get("source_url", ""),
            "latest_supplement_accession": latest_supp.get("accession", ""),
            "latest_supplement_filing_date": latest_supp.get("filing_date", ""),
            "latest_supplement_url": latest_supp.get("source_url", ""),
            "original_adjudication_accession": target.get("accession", ""),
            "original_adjudication_filing_date": target.get("filing_date", ""),
            "manual_strategy_class": target.get("adjudicated_strategy_class", ""),
            "review_status": "candidate_inventory_requires_manual_review",
        })

    inventory_fields = [
        "cik", "series_id", "series_name", "fundno", "form", "document_type",
        "document_description", "filename", "document_kind", "accession", "filing_date",
        "prospectus_date_candidates", "supplement_date_candidates", "effective_date_candidates",
        "match_method", "matched_name_alias", "series_id_in_submission_header",
        "source_url", "source_sha256", "text_length", "strategy_context_excerpt",
    ]
    fund_year_fields = inventory_fields + [
        "fund_year", "asof_cutoff", "filing_age_days",
        "original_adjudication_accession", "original_adjudication_filing_date",
    ]
    summary_fields = [
        "fundno", "fund_year", "series_name", "cik", "series_id", "asof_cutoff",
        "candidate_document_count", "candidate_base_prospectus_count", "candidate_supplement_count",
        "latest_base_or_candidate_accession", "latest_base_or_candidate_filing_date",
        "latest_base_or_candidate_document_kind", "latest_base_or_candidate_url",
        "latest_supplement_accession", "latest_supplement_filing_date", "latest_supplement_url",
        "original_adjudication_accession", "original_adjudication_filing_date",
        "manual_strategy_class", "review_status",
    ]
    series_coverage = []
    for (cik, sid), target in sorted(series_rows.items()):
        docs = [d for d in inventory if d["cik"] == cik and d["series_id"] == sid]
        series_coverage.append({
            "cik": cik,
            "series_id": sid,
            "series_name": target.get("series_name", ""),
            "fundno": target.get("fundno_key", ""),
            "document_links": len(docs),
            "first_filing_date": min((d["filing_date"] for d in docs), default=""),
            "last_filing_date": max((d["filing_date"] for d in docs), default=""),
            "unique_accessions": len({d["accession"] for d in docs}),
            "original_adjudication_accession_found": any(
                d["accession"] == target.get("accession", "") for d in docs
            ),
        })

    write_csv(out / "c1_active30_document_inventory.csv", inventory, inventory_fields)
    write_csv(out / "c1_active30_fund_year_candidates.csv", fund_year_docs, fund_year_fields)
    write_csv(out / "c1_active30_asof_summary.csv", summaries, summary_fields)
    write_csv(out / "c1_active30_series_coverage.csv", series_coverage, [
        "cik", "series_id", "series_name", "fundno", "document_links",
        "first_filing_date", "last_filing_date", "unique_accessions",
        "original_adjudication_accession_found",
    ])
    write_csv(out / "c1_active30_retrieval_errors.csv", errors, ["cik", "accession", "stage", "error"])

    missing_series = [r for r in series_coverage if int(r["document_links"]) == 0]
    zero_candidate_rows = [r for r in summaries if int(r["candidate_document_count"]) == 0]
    metrics = {
        "target_fund_year_rows": len(targets),
        "target_unique_fundnos": len({r["fundno_key"] for r in targets}),
        "target_unique_series": len(series_rows),
        "target_unique_ciks": len({k[0] for k in series_rows}),
        "ciks_processed": ciks_processed,
        "filings_scanned": scanned_filings,
        "documents_downloaded": downloaded_documents,
        "series_document_links": len(inventory),
        "fund_year_document_links": len(fund_year_docs),
        "series_with_documents": len(series_coverage) - len(missing_series),
        "series_without_documents": [r["series_id"] for r in missing_series],
        "fund_years_without_candidate_documents": [
            f'{r["fundno"]}:{r["fund_year"]}' for r in zero_candidate_rows
        ],
        "retrieval_errors": len(errors),
        "start_date": START_DATE.isoformat(),
        "end_date": END_DATE.isoformat(),
        "asof_rule": "filing_date strictly before January 1 of fund_year",
        "strategy_adjudication": "not automated; existing 30 manual active labels are carried for audit only",
    }
    (out / "c1_active30_audit_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual-csv", type=Path, default=Path("research/c1_manual_adjudications.csv"))
    parser.add_argument("--out", type=Path, default=Path("c1_active30_audit"))
    args = parser.parse_args()
    metrics = run(args.manual_csv, args.out)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
