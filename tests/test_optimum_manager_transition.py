import json
import sys
import tempfile
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_optimum_manager_transition import build
from build_c2_cohort_no_trade_drift import flatten_strategy_flags
ROOT=Path(__file__).resolve().parents[1]

def sample_holdings():
    rows=[]
    weights={"2025-06-30":[("A",50),("B",30),("C",20)],"2025-09-30":[("A",40),("B",40),("D",20)],"2025-12-31":[("A",30),("D",50),("E",20)]}
    for date,holdings in weights.items():
        for ticker,weight in holdings:
            rows.append({"entity":"Optimum Large Cap Growth Fund","report_date":date,"name":f"Company {ticker}","cusip":f"0000000{ticker}","isin":"","ticker":ticker,"pct_net_assets":str(weight)})
    return pd.DataFrame(rows)

def sample_allocations(path):
    pd.DataFrame([
      {"report_date":"2025-09-30","american_century_pct":48.51,"delaware_management_company_pct":0,"los_angeles_capital_pct":51.49},
      {"report_date":"2025-10-31","american_century_pct":48.79,"delaware_management_company_pct":0,"los_angeles_capital_pct":51.21},
      {"report_date":"2025-11-30","american_century_pct":48.65,"delaware_management_company_pct":0,"los_angeles_capital_pct":51.35},
      {"report_date":"2025-12-31","american_century_pct":48.44,"delaware_management_company_pct":0,"los_angeles_capital_pct":51.56},
    ]).to_csv(path,index=False)

class OptimumTransitionTests(unittest.TestCase):
    def test_three_filing_comparison_and_allocation_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); holdings=root/"holdings.csv"; allocations=root/"allocations.csv"
            sample_holdings().to_csv(holdings,index=False); sample_allocations(allocations)
            result=build(holdings,allocations,root/"out")
            self.assertEqual([x["unique_securities"] for x in result["filing_summary"]],[3,3,3])
            first,second=result["interval_summary"]
            self.assertEqual((first["continuing_securities"],first["added_at_end_date"],first["absent_at_end_date"]),(2,1,1))
            self.assertEqual((second["continuing_securities"],second["added_at_end_date"],second["absent_at_end_date"]),(2,1,1))
            self.assertAlmostEqual(result["allocation_change"]["american_century_change_sep_to_dec_pp"],-0.07,places=8)
            self.assertAlmostEqual(result["allocation_change"]["los_angeles_capital_change_sep_to_dec_pp"],0.07,places=8)
            self.assertTrue((root/"out"/"OPTIMUM_THREE_FILING_TRANSITION_AUDIT.md").exists())
            self.assertTrue((root/"out"/"optimum_three_filing_security_changes.csv").exists())

    def test_missing_required_allocation_month_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); allocations=root/"alloc.csv"; holdings=root/"holdings.csv"
            sample_allocations(allocations); pd.read_csv(allocations).iloc[:-1].to_csv(allocations,index=False)
            sample_holdings().to_csv(holdings,index=False)
            with self.assertRaises(ValueError): build(holdings,allocations,root/"out")

    def test_structural_flag_distinguishes_agreement_from_manager_name_change(self):
        payload=json.loads((ROOT/"research"/"C2_COHORT_FUND_FLAGS.json").read_text())
        flat=flatten_strategy_flags(payload["funds"]["Optimum Large Cap Growth Fund"])
        self.assertFalse(flat["manager_change_within_window"])
        self.assertFalse(flat["investment_manager_name_changed_within_window"])
        self.assertTrue(flat["manager_ownership_or_control_change_within_window"])
        self.assertTrue(flat["advisory_agreement_replaced_within_window"])
        self.assertTrue(flat["subadvisers_continued"])
        self.assertTrue(flat["published_aggregate_subadviser_allocation_stable"])
        self.assertFalse(flat["day_to_day_portfolio_management_change_established"])

    def test_dated_portfolio_manager_roster_comparison(self):
        roster = pd.read_csv(ROOT/"research"/"OPTIMUM_PORTFOLIO_MANAGER_ROSTER_COMPARISON_2025_2026.csv")
        self.assertEqual(len(roster), 6)
        self.assertEqual(roster["portfolio_manager"].nunique(), 6)
        self.assertTrue((roster["fund_start_date"].notna()).all())
        self.assertTrue(roster["roster_comparison"].str.contains("Same person").all())
        bourke = roster.loc[roster["portfolio_manager"].str.startswith("Jeff Bourke")].iloc[0]
        self.assertIn("Vice President, Portfolio Manager", bourke["pre_transition_title_as_of_2025_03_31"])
        self.assertIn("Vice President, Senior Portfolio Manager", bourke["post_transition_title_as_of_2026_03_31"])
        flags = json.loads((ROOT/"research"/"C2_COHORT_FUND_FLAGS.json").read_text())
        optimum = flags["funds"]["Optimum Large Cap Growth Fund"]
        self.assertTrue(optimum["named_portfolio_manager_roster_unchanged_in_reviewed_filings"])
        self.assertTrue(optimum["portfolio_manager_responsibility_descriptions_consistent_in_reviewed_filings"])
        self.assertFalse(optimum["day_to_day_portfolio_management_change_established"])

    def test_real_run21_optimum_counts_and_composition_metrics(self):
        path=Path("/mnt/data/c2run21/nport_cohort_common_equity.csv")
        if not path.exists(): self.skipTest("Run #21 artifact not mounted")
        with tempfile.TemporaryDirectory() as tmp:
            allocations=Path(tmp)/"alloc.csv"
            pd.read_csv(ROOT/"research"/"OPTIMUM_SUBADVISER_ALLOCATIONS_2025.csv").to_csv(allocations,index=False)
            result=build(path,allocations,Path(tmp)/"out")
            self.assertEqual([x["unique_securities"] for x in result["filing_summary"]],[126,117,118])
            self.assertAlmostEqual(result["interval_summary"][0]["one_way_composition_distance_pp"],16.9290682691,places=7)
            self.assertAlmostEqual(result["interval_summary"][1]["one_way_composition_distance_pp"],14.5592699035,places=7)

if __name__=="__main__": unittest.main()
