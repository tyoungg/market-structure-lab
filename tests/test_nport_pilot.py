import importlib.util
from pathlib import Path
import unittest
import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_nport_pilot.py"
spec = importlib.util.spec_from_file_location("run_nport_pilot", SCRIPT)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)

class NoTradeMathTests(unittest.TestCase):
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
