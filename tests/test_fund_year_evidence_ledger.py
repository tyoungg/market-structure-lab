import sys
import unittest
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_fund_year_evidence_ledger import dates, item69_candidate, nsar_eligible


class FundYearEvidenceLedgerTests(unittest.TestCase):
    def test_mixed_sec_date_formats(self):
        got = dates(pd.Series(["10/31/2006", "2006-10-31", "", "bad"]))
        self.assertEqual(got.iloc[0], pd.Timestamp("2006-10-31"))
        self.assertEqual(got.iloc[1], pd.Timestamp("2006-10-31"))
        self.assertTrue(pd.isna(got.iloc[2]))
        self.assertTrue(pd.isna(got.iloc[3]))

    def test_item69_n_is_not_active(self):
        self.assertEqual(item69_candidate("Y"), "passive_index_candidate")
        self.assertEqual(item69_candidate("N"), "not_reported_as_index_not_active")
        self.assertNotEqual(item69_candidate("N"), "active")

    def test_nsar_asof_cutoff_and_548_day_rule(self):
        cutoff = pd.Timestamp("2008-01-01")
        self.assertTrue(nsar_eligible(pd.Timestamp("2007-12-31"), pd.Timestamp("2007-10-31"), cutoff))
        self.assertFalse(nsar_eligible(pd.Timestamp("2008-01-01"), pd.Timestamp("2007-10-31"), cutoff))
        self.assertFalse(nsar_eligible(pd.Timestamp("2007-12-31"), pd.Timestamp("2006-06-30"), cutoff))
        self.assertFalse(nsar_eligible(pd.Timestamp("2007-12-31"), pd.NaT, cutoff))


if __name__ == "__main__":
    unittest.main()
