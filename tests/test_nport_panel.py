import importlib.util
from pathlib import Path
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_nport_panel", ROOT / "scripts" / "run_nport_panel.py")
panel = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(panel)


class NportPanelTests(unittest.TestCase):
    def test_identifier_bridge_aggregates_one_to_many_rows(self):
        ids = pd.DataFrame({
            "HOLDING_ID": [1, 1, 2],
            "IDENTIFIER_ISIN": ["US0000000001", "US0000000001", ""],
            "IDENTIFIER_TICKER": ["ABC", "ABC", ""],
            "IDENTIFIERS_ID": [1, 2, 3],
            "OTHER_IDENTIFIER": ["", "", ""],
            "OTHER_IDENTIFIER_DESC": ["", "", ""],
        })
        bridge = panel.build_identifier_bridge(ids)
        self.assertEqual(len(bridge), 2)
        first = bridge.set_index("HOLDING_ID").loc["1"]
        self.assertEqual(first.ISIN, "US0000000001")
        self.assertEqual(first.ISIN_COUNT, 1)
        self.assertEqual(first.IDENTIFIER_ROWS, 2)

    def test_ambiguous_isin_falls_back_to_cusip(self):
        holdings = pd.DataFrame({
            "ACCESSION_NUMBER": ["a"], "HOLDING_ID": [1], "ISSUER_NAME": ["Issuer"],
            "ISSUER_CUSIP": ["123456789"], "PERCENTAGE": ["10"], "ASSET_CAT": ["EC"],
        })
        ids = pd.DataFrame({
            "HOLDING_ID": ["1", "1"], "IDENTIFIER_ISIN": ["US0000000001", "US0000000002"],
            "IDENTIFIER_TICKER": ["ABC", "ABC"], "IDENTIFIERS_ID": [1, 2],
            "OTHER_IDENTIFIER": ["", ""], "OTHER_IDENTIFIER_DESC": ["", ""],
        })
        for col in ["ISSUER_TITLE", "BALANCE", "UNIT", "CURRENCY_CODE", "CURRENCY_VALUE",
                    "EXCHANGE_RATE", "PAYOFF_PROFILE", "ISSUER_TYPE", "INVESTMENT_COUNTRY"]:
            holdings[col] = ""
        got = panel.attach_identifiers(holdings, ids)
        self.assertEqual(got.iloc[0].SECURITY_KEY, "123456789")
        self.assertEqual(got.iloc[0].IDENTITY_STATUS, "AMBIGUOUS_ISIN")

    def test_equity_weights_normalize_only_common_equity(self):
        holdings = pd.DataFrame({
            "ACCESSION_NUMBER": ["a", "a", "a"],
            "ASSET_CAT": ["EC", "EC", "STIV"],
            "PCT_NAV": [0.40, 0.20, 0.40],
            "SECURITY_KEY": ["A", "B", "C"],
            "ISSUER_NAME": ["A Co", "B Co", "Cash"],
            "ISSUER_CUSIP": ["", "", ""], "ISIN": ["", "", ""],
            "TICKER": ["", "", ""], "IDENTITY_STATUS": ["CUSIP_FALLBACK"] * 3,
            "HOLDING_ID": [1, 2, 3],
        })
        weights, equity_share = panel.equity_weights(holdings, "a")
        self.assertAlmostEqual(equity_share, 0.60)
        self.assertAlmostEqual(weights.EQUITY_WEIGHT.sum(), 1.0)
        self.assertEqual(set(weights.SECURITY_KEY), {"A", "B"})

    def test_strict_no_trade_requires_every_position_return(self):
        start = pd.DataFrame({"SECURITY_KEY": ["A", "B"], "EQUITY_WEIGHT": [0.6, 0.4]})
        complete = pd.DataFrame({"SECURITY_KEY": ["A", "B"], "RETURN": [0.10, -0.10]})
        nt, coverage, missing = panel.strict_no_trade(start, complete)
        self.assertIsNotNone(nt)
        self.assertAlmostEqual(coverage, 1.0)
        self.assertEqual(missing, [])
        partial = pd.DataFrame({"SECURITY_KEY": ["A"], "RETURN": [0.10]})
        nt, coverage, missing = panel.strict_no_trade(start, partial)
        self.assertIsNone(nt)
        self.assertAlmostEqual(coverage, 0.6)
        self.assertEqual(missing, ["B"])


if __name__ == "__main__":
    unittest.main()
