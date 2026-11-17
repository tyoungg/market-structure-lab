"""Read-only loaders for the N-PORT Streamlit dashboard."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data" / "nport_dashboard"

def load_dashboard_data(data_dir: str | Path | None = None) -> dict:
    """Load compact, versioned dashboard outputs; never run calculations."""
    folder = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    files = {
        "summary": folder / "panel_summary.json",
        "results": folder / "fund_interval_results.csv",
        "availability": folder / "observation_availability.csv",
        "uncovered": folder / "uncovered_positions.csv",
        "crosswalk": folder / "security_crosswalk.csv",
        "filings": folder / "filing_resolution.csv",
        "funds": folder / "sample_funds.csv",
    }
    data = {"data_dir": folder, "available": False}
    if files["summary"].exists():
        data["summary"] = json.loads(files["summary"].read_text(encoding="utf-8"))
    for key in ("results", "availability", "uncovered", "crosswalk", "filings", "funds"):
        source = files[key]
        if key == "funds" and not source.exists():
            source = ROOT / "data" / "nport_panel" / "sample_funds.csv"
        data[key] = pd.read_csv(source) if source.exists() else pd.DataFrame()
    data["available"] = bool(data.get("summary")) and not data["results"].empty
    return data
