import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_c2_nport_cohort import read_manifest, validate_manifest


def sample_manifest():
    rows = []
    funds = [
        ("Optimum Large Cap Growth Fund", "growth", "0001227523", "S000002422"),
        ("Fidelity Contrafund", "growth", "0000024238", "S000006037"),
        ("JPMorgan Large Cap Growth Fund", "growth", "0000763852", "S000003856"),
        ("JPMorgan Large Cap Value Fund", "value", "0000763852", "S000003857"),
        ("Fidelity Magellan Fund", "blend", "0000061397", "S000007112"),
        ("Oakmark Fund", "value", "0000872323", "S000002758"),
    ]
    for entity, style, cik, series in funds:
        for date in ("2025-06-30", "2025-09-30", "2025-12-31"):
            rows.append({
                "entity":entity,"role":"fund","style_bucket":style,"report_date":date,
                "cik":cik,"series_id":series,"series_name":entity,
                "accession":f"{cik}-{date}","url":f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/x/primary_doc.xml"
            })
    for entity, role, cik, series, name in [
        ("SPY","benchmark_sp500","0000884394","","SPDR S&P 500 ETF Trust"),
        ("IWB","benchmark_russell1000","0001100663","S000004347","iShares Russell 1000 ETF"),
    ]:
        for date in ("2025-06-30", "2025-09-30", "2025-12-31"):
            rows.append({
                "entity":entity,"role":role,"style_bucket":"","report_date":date,
                "cik":cik,"series_id":series,"series_name":name,
                "accession":f"{cik}-{date}","url":f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/x/primary_doc.xml"
            })
    return rows


class C2CohortManifestTests(unittest.TestCase):
    def test_valid_six_fund_manifest(self):
        rows = sample_manifest()
        validate_manifest(rows)
        self.assertEqual(len(rows), 24)

    def test_wrong_date_fails(self):
        rows = sample_manifest()
        rows[0]["report_date"] = "2025-07-31"
        with self.assertRaises(ValueError):
            validate_manifest(rows)

    def test_duplicate_entity_date_fails(self):
        rows = sample_manifest()
        rows[-1] = dict(rows[-2])
        with self.assertRaises(ValueError):
            validate_manifest(rows)

    def test_wrong_cohort_size_fails(self):
        rows = sample_manifest()[:-1]
        with self.assertRaises(ValueError):
            validate_manifest(rows)

    def test_read_manifest_csv(self):
        rows = sample_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            loaded = read_manifest(path)
            validate_manifest(loaded)
            self.assertEqual(len(loaded), 24)


if __name__ == "__main__":
    unittest.main()
