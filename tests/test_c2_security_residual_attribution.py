import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_c2_security_residual_attribution import (
    build_attribution,
    normalized_end_weights,
    security_residual_contributions,
)


class C2SecurityResidualAttributionTests(unittest.TestCase):
    def test_security_contributions_sum_to_active_share_residual(self):
        actual = {"A": 0.60, "B": 0.40}
        no_trade = {"A": 0.55, "B": 0.45}
        benchmark = {"A": 0.50, "B": 0.50}
        contributions = security_residual_contributions(actual, no_trade, benchmark)
        self.assertAlmostEqual(sum(contributions.values()), 5.0, places=10)

    def test_end_portfolio_normalizes_by_common_equity_sleeve(self):
        holdings = pd.DataFrame([
            {"entity": "ETF", "report_date": "2025-12-31", "is_common_equity": "True",
             "pct_net_assets": "6", "isin": "US0000000001", "cusip": "", "ticker": "A", "name": "Alpha"},
            {"entity": "ETF", "report_date": "2025-12-31", "is_common_equity": "True",
             "pct_net_assets": "4", "isin": "US0000000002", "cusip": "", "ticker": "B", "name": "Beta"},
            {"entity": "ETF", "report_date": "2025-12-31", "is_common_equity": "False",
             "pct_net_assets": "90", "isin": "US0000000003", "cusip": "", "ticker": "C", "name": "Cash-like"},
        ])
        weights, names = normalized_end_weights(holdings, "ETF", "2025-12-31")
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertAlmostEqual(weights["ISIN:US0000000001"], 0.6)
        self.assertAlmostEqual(weights["ISIN:US0000000002"], 0.4)
        self.assertEqual(names["ISIN:US0000000001"], "Alpha")

    def test_full_build_reconciles_and_preserves_structural_flags(self):
        holdings = pd.DataFrame([
            {"entity": "ETF", "report_date": "2025-12-31", "is_common_equity": "True",
             "pct_net_assets": "50", "isin": "US0000000001", "cusip": "", "ticker": "A", "name": "Alpha"},
            {"entity": "ETF", "report_date": "2025-12-31", "is_common_equity": "True",
             "pct_net_assets": "50", "isin": "US0000000002", "cusip": "", "ticker": "B", "name": "Beta"},
        ])
        drift = pd.DataFrame([
            {"fund": "Fund", "security_id": "ISIN:US0000000001", "name": "Alpha",
             "actual_end_weight_pct_equity": 60, "no_trade_end_weight_pct_equity": 55},
            {"fund": "Fund", "security_id": "ISIN:US0000000002", "name": "Beta",
             "actual_end_weight_pct_equity": 40, "no_trade_end_weight_pct_equity": 45},
        ])
        decompositions = pd.DataFrame([{
            "fund": "Fund", "benchmark_entity": "ETF", "calculation_status": "calculated",
            "actual_portfolio_change_beyond_drift_pp": 5.0,
            "strategy_classification": "Growth", "strategy_group": "growth",
            "manager_change_within_window": True, "manager_change_effective_date": "2025-12-01",
            "non_diversified_status": False, "non_diversified_effective_date": "",
            "fee_limit_change_effective_date": "", "structural_change_flag_ids": "manager_transition",
        }])
        attribution, summary = build_attribution(holdings, drift, decompositions, "2025-12-31")
        self.assertAlmostEqual(attribution["residual_contribution_pp"].sum(), 5.0, places=10)
        self.assertAlmostEqual(summary.iloc[0]["reconciliation_error_pp"], 0.0, places=10)
        self.assertTrue(summary.iloc[0]["manager_change_within_window"])
        self.assertEqual(summary.iloc[0]["manager_change_effective_date"], "2025-12-01")
        self.assertEqual(len(attribution), 2)

    def test_missing_end_date_portfolio_fails_closed(self):
        holdings = pd.DataFrame([{
            "entity": "ETF", "report_date": "2025-09-30", "is_common_equity": "True",
            "pct_net_assets": "100", "isin": "US0000000001", "cusip": "", "ticker": "A", "name": "Alpha",
        }])
        with self.assertRaises(ValueError):
            normalized_end_weights(holdings, "ETF", "2025-12-31")


if __name__ == "__main__":
    unittest.main()
