import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from utils.nport_dashboard import load_dashboard_data

class NportDashboardLoaderTests(unittest.TestCase):
    def test_missing_files_return_empty_safe_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = load_dashboard_data(tmp)
        self.assertFalse(data["available"])
        self.assertTrue(data["results"].empty)
        self.assertTrue(data["funds"].empty)

    def test_loads_published_summary_and_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "panel_summary.json").write_text(json.dumps({"expected_fund_intervals": 3}), encoding="utf-8")
            pd.DataFrame([{"STATUS": "CALCULATED"}]).to_csv(folder / "fund_interval_results.csv", index=False)
            data = load_dashboard_data(folder)
        self.assertTrue(data["available"])
        self.assertEqual(data["summary"]["expected_fund_intervals"], 3)
        self.assertEqual(data["results"].iloc[0]["STATUS"], "CALCULATED")

if __name__ == "__main__":
    unittest.main()
