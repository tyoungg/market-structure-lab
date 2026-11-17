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
        valid, chosen = pilot.select_latest_valid_filings(rows)
        self.assertEqual(chosen.iloc[0].ACCESSION_NUMBER,"b")
        self.assertNotIn("c",set(valid.ACCESSION_NUMBER))

    def test_yfinance_price_first_multiindex_columns(self):
        prices = pd.DataFrame(
            [[100.0, 200.0], [101.0, 202.0]],
            columns=pd.MultiIndex.from_tuples([("Close", "AAPL"), ("Close", "SPY")]),
            index=pd.to_datetime(["2026-05-29", "2026-06-30"]),
        )
        got = pilot.extract_close_series(prices, "AAPL")
        self.assertEqual(got.tolist(), [100.0, 101.0])

    def test_yfinance_ticker_first_multiindex_columns(self):
        prices = pd.DataFrame(
            [[100.0, 200.0], [101.0, 202.0]],
            columns=pd.MultiIndex.from_tuples([("AAPL", "Close"), ("SPY", "Close")]),
            index=pd.to_datetime(["2026-05-29", "2026-06-30"]),
        )
        got = pilot.extract_close_series(prices, "AAPL")
        self.assertEqual(got.tolist(), [100.0, 101.0])

    def test_committed_ab_ivv_inputs_reconcile(self):
        root = Path(__file__).resolve().parents[1] / "data" / "nport_pilot_inputs"
        may = pd.read_csv(root / "ab_may_2026_equity.csv")
        june = pd.read_csv(root / "ab_june_2026_equity.csv")
        ivv = pd.read_csv(root / "ivv_june_2026_compact_equity.csv")
        self.assertEqual(len(may), 62)
        self.assertEqual(len(june), 60)
        self.assertEqual(len(ivv), 50)
        for frame in (may, june, ivv):
            self.assertAlmostEqual(float(frame.EQUITY_WEIGHT.sum()), 1.0, places=6)
            self.assertFalse(frame.SECURITY_KEY.duplicated().any())
        self.assertAlmostEqual(pilot.active_share(june, ivv), 0.7717531503065802, places=6)

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
