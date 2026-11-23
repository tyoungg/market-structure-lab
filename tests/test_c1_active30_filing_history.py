import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_c1_active30_filing_history as audit


class TestC1Active30FilingHistory(unittest.TestCase):
    def test_strict_cutoff_excludes_filing_on_cutoff(self):
        cutoff = audit.parse_date("2009-01-01")
        self.assertTrue(audit.strict_asof(audit.parse_date("2008-12-31"), cutoff))
        self.assertFalse(audit.strict_asof(audit.parse_date("2009-01-01"), cutoff))
        self.assertFalse(audit.strict_asof(None, cutoff))

    def test_series_header_match_is_explicit(self):
        ok, method, alias = audit.match_series(
            "S000002422", {"S000002422"}, "OPTIMUM LARGE CAP GROWTH FUND"
        )
        self.assertTrue(ok)
        self.assertEqual(method, "header_and_name")
        self.assertEqual(alias, "OPTIMUM LARGE CAP GROWTH FUND")

    def test_series_ids_are_read_only_from_submission_header(self):
        text = (
            "<SEC-HEADER>\n<SERIES>\n<SERIES-ID>S000002422\n</SERIES>\n"
            "</SEC-HEADER>\n<DOCUMENT>\n<TEXT>Body mentions S000002424</TEXT>\n"
        )
        self.assertEqual(
            audit.extract_series_ids_from_submission_header(text),
            {"S000002422"},
        )

    def test_name_alias_match_is_explicit(self):
        ok, method, alias = audit.match_series(
            "S000000667", set(), "Legg Mason Opportunity Trust"
        )
        self.assertTrue(ok)
        self.assertEqual(method, "name_alias")
        self.assertEqual(alias, "Legg Mason Opportunity Trust")

    def test_unmatched_name_and_header_fail_closed(self):
        ok, method, alias = audit.match_series(
            "S000002422", {"S000000001"}, "A different fund prospectus"
        )
        self.assertFalse(ok)
        self.assertEqual(method, "")
        self.assertEqual(alias, "")

    def test_supplement_detected_before_generic_prospectus(self):
        text = "Supplement to the Funds' Prospectuses dated July 29, 2007."
        self.assertEqual(audit.classify_document(text, "497"), "supplement")

    def test_sai_detected(self):
        text = "STATEMENT OF ADDITIONAL INFORMATION. This SAI should be read with the prospectus."
        self.assertEqual(audit.classify_document(text, "485BPOS"), "sai")

    def test_prospectus_date_extracted(self):
        text = "PROSPECTUS\nDecember 31, 2008\n\nInvestment Objective"
        prospectus, supplement, effective = audit.extract_dates(text)
        self.assertIn("December 31, 2008", prospectus)
        self.assertEqual(supplement, "")
        self.assertEqual(effective, "")

    def test_supplement_and_effective_dates_extracted(self):
        text = (
            "Supplement to the Fund's Prospectus dated July 29, 2008. "
            "This supplement is dated December 17, 2008. "
            "The sub-adviser will begin serving on or about December 17, 2008."
        )
        prospectus, supplement, effective = audit.extract_dates(text)
        self.assertIn("July 29, 2008", prospectus)
        self.assertIn("December 17, 2008", supplement)
        self.assertIn("December 17, 2008", effective)


if __name__ == "__main__":
    unittest.main()
