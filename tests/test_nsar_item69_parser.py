import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_nsar_item69 import parse_item7_item69, parse_sec_dates


class TestNSARItem69(unittest.TestCase):
    def test_period_series_names_and_flags(self):
        body = "\n".join([
            "000 B000000 12/31/2008",
            "007 C010100  1",
            "007 C020100 Example Index Fund",
            "007 C030100 N",
            "007 C010300  3",
            "007 C020300 Example Active Fund",
            "007 C030300 N",
            "069  000100 Y",
            "069  000300 N",
            "069  000000 N",
        ])
        names, flags, report_date = parse_item7_item69(body)
        self.assertEqual(report_date, "12/31/2008")
        self.assertEqual(names, {"01": "Example Index Fund", "03": "Example Active Fund"})
        self.assertEqual([(x["series_ordinal"], x["value"], x["scope"]) for x in flags],
                         [("01", "Y", "series"), ("03", "N", "series"), ("00", "N", "registrant")])

    def test_semiannual_report_date(self):
        _, _, report_date = parse_item7_item69("000 A000000 05/31/2008\n069 000100 Y")
        self.assertEqual(report_date, "05/31/2008")

    def test_blank_period_remains_blank(self):
        _, _, report_date = parse_item7_item69("069 000100 Y")
        self.assertEqual(report_date, "")

    def test_iso_period_date(self):
        _, _, report_date = parse_item7_item69("000 B000000 2006-10-31\n069 000100 Y")
        self.assertEqual(report_date, "2006-10-31")

    def test_mixed_sec_date_formats(self):
        parsed = parse_sec_dates(pd.Series(["10/31/2006", "2006-10-31", "12/31/2005"]))
        self.assertEqual(parsed.dt.strftime("%Y-%m-%d").tolist(),
                         ["2006-10-31", "2006-10-31", "2005-12-31"])
        self.assertFalse(parsed.isna().any())


if __name__ == "__main__":
    unittest.main()
