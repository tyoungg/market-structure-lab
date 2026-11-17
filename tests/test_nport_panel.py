import importlib.util
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

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

    def test_shared_security_ticker_conflict_is_not_silently_collapsed(self):
        a = pd.DataFrame([{
            "SECURITY_KEY": "US0000000001", "ISIN": "US0000000001",
            "ISSUER_CUSIP": "000000001", "TICKER": "ABC",
            "ISSUER_NAME": "ABC Corp", "IDENTITY_STATUS": "ISIN",
        }])
        b = pd.DataFrame([{
            "SECURITY_KEY": "US0000000001", "ISIN": "US0000000001",
            "ISSUER_CUSIP": "000000001", "TICKER": "ABC.A",
            "ISSUER_NAME": "ABC Corporation", "IDENTITY_STATUS": "ISIN",
        }])
        got = panel.aggregate_starting_security_candidates([a, b]).iloc[0]
        self.assertEqual(got.TICKER, "")
        self.assertTrue(got.TICKER_CONFLICT)
        self.assertEqual(got.SOURCE_FUND_COUNT, 2)
        self.assertIn("ABC", got.TICKER_CANDIDATES)

    def test_actual_fund_report_dates_pair_consecutively_and_match_benchmark_end(self):
        portfolios = {
            ("FUND_A", "2025-10-31"): pd.DataFrame(),
            ("FUND_A", "2026-01-31"): pd.DataFrame(),
            ("FUND_A", "2026-04-30"): pd.DataFrame(),
            ("IVV", "2026-01-31"): pd.DataFrame(),
            # Deliberately no IVV observation for April 30.
        }
        schedule = panel.build_interval_schedule(portfolios, {"FUND_A"}, "IVV")
        self.assertEqual(len(schedule), 2)
        self.assertEqual(schedule[0]["START_DATE"], "2025-10-31")
        self.assertEqual(schedule[0]["END_DATE"], "2026-01-31")
        self.assertEqual(schedule[0]["STATUS"], "READY")
        self.assertEqual(schedule[1]["END_DATE"], "2026-04-30")
        self.assertEqual(schedule[1]["STATUS"], "BENCHMARK_OBSERVATION_MISSING_ON_FUND_END_DATE")

    def test_long_report_date_gap_is_flagged(self):
        portfolios = {
            ("FUND_A", "2025-10-31"): pd.DataFrame(),
            ("FUND_A", "2026-05-31"): pd.DataFrame(),
            ("IVV", "2026-05-31"): pd.DataFrame(),
        }
        schedule = panel.build_interval_schedule(portfolios, {"FUND_A"}, "IVV")
        self.assertEqual(schedule[0]["STATUS"], "REPORT_DATE_GAP_OVER_150_DAYS")

    def test_nport_ticker_is_available_as_mapping_candidate(self):
        self.assertEqual(panel.pilot.nport_ticker_candidate({"TICKER": "BRK.B"}), "BRK-B")
        self.assertEqual(panel.pilot.nport_ticker_candidate({"TICKER": ""}), "")

    def test_dated_ticker_override_before_effective_date_uses_old_symbol(self):
        override = {
            "OLD_TICKER": "MMC", "NEW_TICKER": "MRSH",
            "EFFECTIVE_DATE": "2026-01-14",
        }
        self.assertEqual(
            panel.pilot.resolve_dated_ticker_pair(override, "2025-09-30", "2025-12-31"),
            ("MMC", "MMC"),
        )

    def test_dated_ticker_override_straddling_effective_date_uses_both_symbols(self):
        override = {
            "OLD_TICKER": "MMC", "NEW_TICKER": "MRSH",
            "EFFECTIVE_DATE": "2026-01-14",
        }
        self.assertEqual(
            panel.pilot.resolve_dated_ticker_pair(override, "2025-12-31", "2026-03-31"),
            ("MMC", "MRSH"),
        )

    def test_dated_ticker_override_after_effective_date_uses_new_symbol(self):
        override = {
            "OLD_TICKER": "BK", "NEW_TICKER": "BNY",
            "EFFECTIVE_DATE": "2026-05-21",
        }
        self.assertEqual(
            panel.pilot.resolve_dated_ticker_pair(override, "2026-06-30", "2026-09-30"),
            ("BNY", "BNY"),
        )

    def test_dated_ticker_change_effective_date_is_inclusive(self):
        override = {
            "OLD_TICKER": "BK", "NEW_TICKER": "BNY",
            "EFFECTIVE_DATE": "2026-05-21",
        }
        self.assertEqual(
            panel.pilot.resolve_dated_ticker_pair(override, "2026-05-20", "2026-05-21"),
            ("BK", "BNY"),
        )

    def test_dated_override_covers_old_and_new_cross_fund_candidates(self):
        row = {"TICKER_CANDIDATES": '["MMC", "MRSH"]'}
        override = {"OLD_TICKER": "MMC", "NEW_TICKER": "MRSH"}
        self.assertTrue(panel.pilot.dated_override_covers_ticker_candidates(row, override))

    def test_dated_override_does_not_suppress_unrelated_cross_fund_candidate(self):
        row = {"TICKER_CANDIDATES": '["MMC", "XYZ"]'}
        override = {"OLD_TICKER": "MMC", "NEW_TICKER": "MRSH"}
        self.assertFalse(panel.pilot.dated_override_covers_ticker_candidates(row, override))

    def test_dated_override_covers_only_explained_openfigi_conflict(self):
        override = {"OLD_TICKER": "MMC", "NEW_TICKER": "MRSH"}
        explained = {"existing_candidate": "MRSH", "openfigi_candidate": "MMC"}
        unrelated = {"existing_candidate": "MRSH", "openfigi_candidate": "XYZ"}
        self.assertTrue(panel.pilot.dated_override_covers_mapping_conflict(explained, override))
        self.assertFalse(panel.pilot.dated_override_covers_mapping_conflict(unrelated, override))

    def test_fetch_returns_uses_old_and_new_symbols_at_interval_endpoints(self):
        dates = pd.to_datetime([
            "2025-12-31", "2026-01-12", "2026-01-13",
            "2026-01-14", "2026-01-15", "2026-03-31",
        ])
        columns = pd.MultiIndex.from_tuples([
            ("MMC", "Close"), ("MRSH", "Close"), ("SPY", "Close")
        ])
        prices = pd.DataFrame([
            [100.0, 100.0, 200.0],
            [101.0, 101.0, 201.0],
            [102.0, 102.0, 202.0],
            [103.0, 103.0, 203.0],
            [104.0, 104.0, 204.0],
            [105.0, 110.0, 220.0],
        ], index=dates, columns=columns)

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return [{
                    "data": [{
                        "exchCode": "US", "ticker": "MMC",
                        "name": "Marsh McLennan",
                        "securityType": "Common Stock",
                        "securityType2": "Common Stock",
                        "figi": "BBG000000MMC",
                    }]
                }]

        start = pd.DataFrame([{
            "SECURITY_KEY": "US5717481023",
            "ISIN": "US5717481023",
            "ISSUER_CUSIP": "571748102",
            "TICKER": "MMC",
            "TICKER_CONFLICT": False,
            "TICKER_CANDIDATES": '["MMC"]',
            "ISSUER_NAME": "Marsh McLennan",
        }])

        with patch("requests.Session.post", return_value=FakeResponse()), \
             patch("time.sleep"), \
             patch.dict(sys.modules, {"yfinance": SimpleNamespace(download=lambda *args, **kwargs: prices)}):
            result = panel.pilot.fetch_returns(start, "2025-12-31", "2026-03-31")

        row = result.iloc[0]
        self.assertEqual(row.START_TICKER, "MMC")
        self.assertEqual(row.END_TICKER, "MRSH")
        self.assertEqual(row.TICKER_TRANSITION_CHECK_STATUS, "MATCH")
        self.assertEqual(row.PRICE_STATUS, "ENDPOINT_PRICES_AVAILABLE")
        self.assertAlmostEqual(float(row.RETURN), 0.10, places=6)

    def test_workflow_cancels_superseded_runs_and_blocks_stale_publish(self):
        workflow = (ROOT / ".github" / "workflows" / "nport-multi-quarter-panel.yml").read_text()
        self.assertIn("cancel-in-progress: true", workflow)
        self.assertIn('TRIGGER_SHA="${GITHUB_SHA:?GITHUB_SHA is required}"', workflow)
        self.assertIn('if [[ "$REMOTE_SHA" != "$TRIGGER_SHA" ]]', workflow)

    def test_ticker_transition_price_histories_must_overlap_and_match(self):
        dates = pd.to_datetime(["2026-01-12", "2026-01-13", "2026-01-14", "2026-01-15"])
        old = pd.Series([100.0, 101.0, 102.0, 103.0], index=dates)
        new = pd.Series([100.0, 101.0, 102.0, 103.0], index=dates)
        result = panel.pilot.compare_ticker_price_series(old, new, "2026-01-14")
        self.assertEqual(result["status"], "MATCH")
        self.assertEqual(result["overlap_days"], 4)
        self.assertAlmostEqual(result["max_abs_price_diff_pct"], 0.0)

    def test_ticker_transition_price_history_mismatch_is_rejected(self):
        dates = pd.to_datetime(["2026-01-12", "2026-01-13", "2026-01-14", "2026-01-15"])
        old = pd.Series([100.0, 101.0, 102.0, 103.0], index=dates)
        new = pd.Series([100.0, 101.0, 104.0, 105.0], index=dates)
        result = panel.pilot.compare_ticker_price_series(old, new, "2026-01-14")
        self.assertEqual(result["status"], "MISMATCH")
        self.assertGreater(result["max_abs_price_diff_pct"], 0.5)

    def test_ticker_transition_without_sufficient_overlap_is_not_approved(self):
        old_dates = pd.to_datetime(["2026-01-05", "2026-01-06"])
        new_dates = pd.to_datetime(["2026-01-14", "2026-01-15"])
        old = pd.Series([100.0, 101.0], index=old_dates)
        new = pd.Series([102.0, 103.0], index=new_dates)
        result = panel.pilot.compare_ticker_price_series(old, new, "2026-01-14")
        self.assertEqual(result["status"], "INSUFFICIENT_OVERLAP")

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
