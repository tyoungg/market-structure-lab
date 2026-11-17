import importlib.util
from pathlib import Path
import unittest
import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_nport_pilot.py"
spec = importlib.util.spec_from_file_location("run_nport_pilot", SCRIPT)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)

class NoTradeMathTests(unittest.TestCase):
    def test_late_notice_is_not_a_portfolio_observation(self):
        rows = pd.DataFrame({
            "FUND_KEY":["F1","F1","F1"],
            "REPORT_DT":pd.to_datetime(["2026-06-30"]*3),
            "FILING_DT":pd.to_datetime(["2026-08-25","2026-08-27","2026-08-29"]),
            "SUB_TYPE":["NPORT-P","NPORT-P/A","NT NPORT-P"],
            "ACCESSION_NUMBER":["a","b","c"],
        })
        valid = rows[rows.SUB_TYPE.isin(["NPORT-P","NPORT-P/A"])].copy()
        valid["SUBTYPE_RANK"] = valid.SUB_TYPE.map({"NPORT-P":1,"NPORT-P/A":2})
        valid = valid.sort_values(["FUND_KEY","REPORT_DT","FILING_DT","SUBTYPE_RANK","ACCESSION_NUMBER"])
        chosen = valid.drop_duplicates(["FUND_KEY","REPORT_DT"],keep="last")
        self.assertEqual(chosen.iloc[0].ACCESSION_NUMBER,"b")
        self.assertNotIn("c",set(chosen.ACCESSION_NUMBER))

    def test_active_share(self):
        a = pd.DataFrame({"SECURITY_KEY":["A","B"],"EQUITY_WEIGHT":[.6,.4]})
        b = pd.DataFrame({"SECURITY_KEY":["A","B"],"EQUITY_WEIGHT":[.5,.5]})
        self.assertAlmostEqual(pilot.active_share(a,b),.10)

    def test_no_trade_weights(self):
        start = pd.DataFrame({"SECURITY_KEY":["A","B"],"EQUITY_WEIGHT":[.6,.4]})
        ret = pd.DataFrame({"SECURITY_KEY":["A","B"],"RETURN":[.10,-.10]})
        weights, coverage = pilot.calculate_no_trade(start,ret)
        self.assertAlmostEqual(coverage,1.0)
        self.assertAlmostEqual(weights.set_index("SECURITY_KEY").loc["A","EQUITY_WEIGHT"],.66/1.02)
        self.assertAlmostEqual(weights.EQUITY_WEIGHT.sum(),1.0)

    def test_incomplete_coverage_blocks_strict_estimate(self):
        start = pd.DataFrame({"SECURITY_KEY":["A","B"],"EQUITY_WEIGHT":[.6,.4]})
        ret = pd.DataFrame({"SECURITY_KEY":["A"],"RETURN":[.10]})
        weights, coverage = pilot.calculate_no_trade(start,ret)
        self.assertIsNone(weights)
        self.assertAlmostEqual(coverage,.6)

if __name__=="__main__": unittest.main()
