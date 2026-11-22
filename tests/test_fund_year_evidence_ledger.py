import sys
import unittest
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_fund_year_evidence_ledger import dates, item69_candidate, nsar_eligible, apply_manual_adjudications, prospectus_staleness_sensitivity


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

    def test_manual_item69_y_adjudication_requires_exact_fund_year_series_and_accession(self):
        fy = pd.DataFrame([{
            "fundno_key":"65260","fund_year":2007,"cik_norm":"0000898745","series_id_norm":"S000007016",
            "nsar_index_fund_status_recomputed":"n_sar_index_fund_yes","latest_nsar_flag":"Y",
            "latest_nsar_accessions":"0001325358-06-000577","final_class":"unclassified",
            "candidate_class":"passive_index_candidate","classification_review_status":"pending",
            "final_class_reason":"pending"
        }])
        manual = pd.DataFrame([{
            "evidence_kind":"nsar_item69_fund_year","fundno_key":"65260","fund_year":"2007",
            "cik_norm":"0000898745","series_id_norm":"S000007016","accession":"0001325358-06-000577",
            "raw_response":"Y","item69_coordinate":"001400","adjudicated_strategy_class":"passive_index",
            "review_status":"confirmed_series_specific_item69_y","rationale":"Exact series identity and positive Item 69 response."
        }])
        got = apply_manual_adjudications(fy, manual, pd.DataFrame(columns=['source_type','asof_eligible','fundno_key','fund_year','cik_norm','series_id_norm','accession','candidate_class']))
        self.assertEqual(got.iloc[0].final_class, "passive_index")
        self.assertEqual(got.iloc[0].manual_adjudication_coordinate, "001400")

    def test_manual_item69_adjudication_rejects_wrong_accession(self):
        fy = pd.DataFrame([{
            "fundno_key":"65260","fund_year":2007,"cik_norm":"0000898745","series_id_norm":"S000007016",
            "nsar_index_fund_status_recomputed":"n_sar_index_fund_yes","latest_nsar_flag":"Y",
            "latest_nsar_accessions":"0001325358-06-000577","final_class":"unclassified",
            "candidate_class":"passive_index_candidate","classification_review_status":"pending",
            "final_class_reason":"pending"
        }])
        manual = pd.DataFrame([{
            "evidence_kind":"nsar_item69_fund_year","fundno_key":"65260","fund_year":"2007",
            "cik_norm":"0000898745","series_id_norm":"S000007016","accession":"wrong-accession",
            "raw_response":"Y","item69_coordinate":"001400","adjudicated_strategy_class":"passive_index",
            "review_status":"confirmed_series_specific_item69_y","rationale":"test"
        }])
        with self.assertRaises(ValueError):
            apply_manual_adjudications(fy, manual)

    def test_prospectus_staleness_sensitivity_windows(self):
        items = pd.DataFrame([
            {"source_type":"SEC_prospectus_or_related_filing","asof_eligible":True,"evidence_age_days":100,
             "fundno_key":"1","fund_year":2008,"evidence_event_id":"p1","cik_norm":"0000000001",
             "series_id_norm":"S1","candidate_class":"unclassified"},
            {"source_type":"SEC_prospectus_or_related_filing","asof_eligible":True,"evidence_age_days":400,
             "fundno_key":"2","fund_year":2008,"evidence_event_id":"p2","cik_norm":"0000000002",
             "series_id_norm":"S2","candidate_class":"unclassified"},
            {"source_type":"SEC_prospectus_or_related_filing","asof_eligible":True,"evidence_age_days":800,
             "fundno_key":"3","fund_year":2008,"evidence_event_id":"p3","cik_norm":"0000000003",
             "series_id_norm":"S3","candidate_class":"unclassified"},
            {"source_type":"SEC_prospectus_or_related_filing","asof_eligible":False,"evidence_age_days":20,
             "fundno_key":"4","fund_year":2008,"evidence_event_id":"p4","cik_norm":"0000000004",
             "series_id_norm":"S4","candidate_class":"active"}
        ])
        got = prospectus_staleness_sensitivity(items).set_index("window")
        self.assertEqual(got.loc["365_days","fund_year_evidence_links"],1)
        self.assertEqual(got.loc["730_days","fund_year_evidence_links"],2)
        self.assertEqual(got.loc["1095_days","fund_year_evidence_links"],3)
        self.assertEqual(got.loc["no_expiry","fund_year_evidence_links"],3)
        self.assertEqual(got.loc["no_expiry","active_candidate_links"],0)

    def test_manual_prospectus_active_adjudication_requires_asof_series_evidence(self):
        fy = pd.DataFrame([{
            "fundno_key":"60020","fund_year":2007,"cik_norm":"0001282693","series_id_norm":"S000000758",
            "final_class":"unclassified","candidate_class":"unclassified","classification_review_status":"pending",
            "final_class_reason":"pending"
        }])
        items = pd.DataFrame([{
            "source_type":"SEC_prospectus_or_related_filing","asof_eligible":True,"fundno_key":"60020",
            "fund_year":"2007","cik_norm":"0001282693","series_id_norm":"S000000758",
            "accession":"0000894189-06-000960","candidate_class":"unclassified"
        }])
        manual = pd.DataFrame([{
            "evidence_kind":"prospectus_fund_year","fundno_key":"60020","fund_year":"2007",
            "cik_norm":"0001282693","series_id_norm":"S000000758","accession":"0000894189-06-000960",
            "adjudicated_strategy_class":"other_active_style","panel_eligible":"true",
            "review_status":"confirmed_active_strategy_asof_fund_year","rationale":"Reviewed source strategy."
        }])
        got, got_items = apply_manual_adjudications(fy, manual, items)
        self.assertEqual(got.iloc[0].final_class,"other_active_style")
        self.assertEqual(got_items.iloc[0].candidate_class,"active")
        self.assertEqual(got_items.iloc[0].manual_adjudication_status,"confirmed_active_strategy_asof_fund_year")

    def test_manual_prospectus_adjudication_rejects_post_cutoff_evidence(self):
        fy = pd.DataFrame([{
            "fundno_key":"60020","fund_year":2007,"cik_norm":"0001282693","series_id_norm":"S000000758",
            "final_class":"unclassified","candidate_class":"unclassified","classification_review_status":"pending",
            "final_class_reason":"pending"
        }])
        items = pd.DataFrame([{
            "source_type":"SEC_prospectus_or_related_filing","asof_eligible":False,"fundno_key":"60020",
            "fund_year":"2007","cik_norm":"0001282693","series_id_norm":"S000000758",
            "accession":"0000894189-06-000960","candidate_class":"unclassified"
        }])
        manual = pd.DataFrame([{
            "evidence_kind":"prospectus_fund_year","fundno_key":"60020","fund_year":"2007",
            "cik_norm":"0001282693","series_id_norm":"S000000758","accession":"0000894189-06-000960",
            "adjudicated_strategy_class":"other_active_style","panel_eligible":"true",
            "review_status":"confirmed_active_strategy_asof_fund_year","rationale":"test"
        }])
        with self.assertRaises(ValueError):
            apply_manual_adjudications(fy, manual, items)


if __name__ == "__main__":
    unittest.main()
