import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_c2_no_trade_drift_pilot import active_share, drift_weights, decompose_active_share, security_identifier, yahoo_symbol


class NoTradeDriftTests(unittest.TestCase):
    def test_active_share(self):
        a = {"CUSIP:111111111": 0.6, "CUSIP:222222222": 0.4}
        b = {"CUSIP:111111111": 0.4, "CUSIP:222222222": 0.6}
        self.assertAlmostEqual(active_share(a, b), 0.2, places=10)

    def test_disjoint_portfolios_have_full_active_share(self):
        self.assertAlmostEqual(active_share({"A": 1.0}, {"B": 1.0}), 1.0, places=10)

    def test_drift_weights_normalize_after_total_returns(self):
        got = drift_weights({"A": 0.5, "B": 0.5}, {"A": 0.10, "B": 0.0})
        self.assertAlmostEqual(got["A"], 0.55 / 1.05, places=10)
        self.assertAlmostEqual(got["B"], 0.50 / 1.05, places=10)
        self.assertAlmostEqual(sum(got.values()), 1.0, places=10)

    def test_decomposition_reconciles_actual_active_share_change(self):
        fund0 = {"A": 0.6, "B": 0.4}
        no_trade1 = {"A": 0.55, "B": 0.45}
        fund1 = {"A": 0.5, "B": 0.5}
        bench0 = {"A": 0.5, "B": 0.5}
        bench1 = {"A": 0.45, "B": 0.55}
        got = decompose_active_share(fund0, no_trade1, fund1, bench0, bench1, "test")
        self.assertAlmostEqual(got["component_reconciliation_error_pp"], 0.0, places=8)
        self.assertAlmostEqual(
            got["actual_active_share_change_pp"],
            got["fund_price_drift_component_pp"] + got["benchmark_weight_change_component_pp"]
            + got["actual_portfolio_change_beyond_drift_pp"],
            places=8,
        )

    def test_security_identifier_uses_cusip_then_isin_then_name(self):
        self.assertEqual(security_identifier({"cusip":"123456789","isin":"US1234567890"}),"CUSIP:123456789")
        self.assertEqual(security_identifier({"cusip":"000000000","isin":"US1234567890"}),"ISIN:US1234567890")
        self.assertEqual(security_identifier({"cusip":"000000000","isin":"","name":"Magic Leap"}),"NAME:MAGIC LEAP")

    def test_yahoo_symbol_exchange_mapping(self):
        self.assertEqual(yahoo_symbol("6861","JP3236200006"),"6861.T")
        self.assertEqual(yahoo_symbol("BRK.B","US0846707026"),"BRK-B")


if __name__ == "__main__":
    unittest.main()
