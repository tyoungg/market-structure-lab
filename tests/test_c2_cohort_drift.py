import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_c2_cohort_no_trade_drift import coverage_gate_pass, portfolio
from build_c2_no_trade_drift_pilot import (
    active_share, decompose_active_share, drift_weights,
    local_return_to_usd, yahoo_quote_currency,
)


class C2CohortDriftTests(unittest.TestCase):
    def test_portfolio_uses_security_id_mapping_not_ticker_guess(self):
        holdings = pd.DataFrame([
            {
                "entity": "Fund A", "report_date": "2025-06-30",
                "is_common_equity": "True", "pct_net_assets": "6.0",
                "isin": "US0378331005", "cusip": "037833100",
                "ticker": "", "name": "Apple Inc.",
            },
            {
                "entity": "Fund A", "report_date": "2025-06-30",
                "is_common_equity": "True", "pct_net_assets": "4.0",
                "isin": "US5949181045", "cusip": "594918104",
                "ticker": "MSFT", "name": "Microsoft Corp.",
            },
        ])
        meta, frame = portfolio(
            holdings, "Fund A", "2025-06-30",
            {"ISIN:US0378331005": "AAPL"},
        )
        self.assertEqual(meta["unique_securities"], 2)
        self.assertAlmostEqual(frame["weight"].sum(), 1.0)
        self.assertEqual(
            frame.set_index("security_id").loc["ISIN:US0378331005", "mapped_ticker"],
            "AAPL",
        )
        self.assertEqual(
            frame.set_index("security_id").loc["ISIN:US5949181045", "mapped_ticker"],
            "",
            "unmapped holdings must not be guessed from another field",
        )

    def test_price_gate_is_strict_at_95_percent(self):
        self.assertTrue(coverage_gate_pass(0.95))
        self.assertTrue(coverage_gate_pass(0.951))
        self.assertFalse(coverage_gate_pass(0.949999))

    def test_yahoo_quote_currency_is_explicit_for_japanese_listing(self):
        self.assertEqual(yahoo_quote_currency("6861.T"), "JPY")
        self.assertEqual(yahoo_quote_currency("AAPL"), "USD")
        self.assertEqual(yahoo_quote_currency("ABC.XY"), "UNSUPPORTED")

    def test_jpy_local_return_is_converted_to_usd_with_correct_fx_direction(self):
        # Local stock rises 10%; JPY weakens from 150 to 155 per USD.
        usd_return = local_return_to_usd(0.10, "JPY", 150.0, 155.0)
        self.assertAlmostEqual(usd_return, (1.10 * 150.0 / 155.0) - 1.0, places=12)
        self.assertAlmostEqual(local_return_to_usd(0.10, "USD"), 0.10, places=12)

    def test_non_usd_conversion_fails_closed_without_fx_endpoints(self):
        with self.assertRaises(ValueError):
            local_return_to_usd(0.10, "JPY", 150.0, None)
        with self.assertRaises(ValueError):
            local_return_to_usd(0.10, "EUR", 1.08, 1.10)

    def test_no_trade_weights_sum_to_one_and_decomposition_reconciles(self):
        start = {"A": 0.6, "B": 0.4}
        returns = {"A": 0.10, "B": -0.05}
        no_trade = drift_weights(start, returns)
        self.assertAlmostEqual(sum(no_trade.values()), 1.0)
        actual = {"A": 0.5, "B": 0.5}
        benchmark_start = {"A": 0.5, "B": 0.5}
        benchmark_end = {"A": 0.55, "B": 0.45}
        result = decompose_active_share(
            start, no_trade, actual, benchmark_start, benchmark_end, "ETF proxy"
        )
        self.assertAlmostEqual(result["component_reconciliation_error_pp"], 0.0, places=10)
        self.assertGreaterEqual(active_share(start, benchmark_start), 0.0)
        self.assertLessEqual(active_share(start, benchmark_start), 1.0)


if __name__ == "__main__":
    unittest.main()
