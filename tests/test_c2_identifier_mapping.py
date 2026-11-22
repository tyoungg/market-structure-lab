import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from map_c2_cohort_identifiers import build_security_universe, select_ticker, valid


class C2IdentifierMappingTests(unittest.TestCase):
    def test_placeholder_identifiers_are_invalid(self):
        for value in ("", "N/A", "NA", "NONE", "XXXX", "000000000"):
            self.assertFalse(valid(value))
        self.assertTrue(valid("US0378331005"))

    def test_isin_is_primary_and_cusip_is_fallback(self):
        holdings = pd.DataFrame([{
            "entity": "Fund A", "role": "fund", "report_date": "2025-06-30",
            "is_common_equity": "True", "pct_net_assets": "5.0",
            "isin": "US0378331005", "cusip": "037833100",
            "ticker": "", "name": "Apple Inc.", "investment_country": "US",
        }])
        universe, _ = build_security_universe(holdings)
        self.assertEqual(len(universe), 1)
        self.assertEqual(universe[0]["primary_identifier_type"], "ID_ISIN")
        self.assertEqual(universe[0]["primary_identifier_value"], "US0378331005")
        self.assertEqual(universe[0]["fallback_identifier_type"], "ID_CUSIP")
        self.assertEqual(universe[0]["fallback_identifier_value"], "037833100")

    def test_placeholder_identifier_does_not_become_primary(self):
        holdings = pd.DataFrame([{
            "entity": "Fund A", "role": "fund", "report_date": "2025-06-30",
            "is_common_equity": "True", "pct_net_assets": "2.0",
            "isin": "N/A", "cusip": "000000000", "ticker": "",
            "name": "Unidentified Security", "investment_country": "US",
        }])
        universe, _ = build_security_universe(holdings)
        self.assertEqual(universe[0]["primary_identifier_type"], "")
        self.assertEqual(universe[0]["security_id"], "NAME:UNIDENTIFIED SECURITY")

    def test_unique_us_equity_ticker_is_selected(self):
        matches = [
            {"ticker": "ABC", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "US", "figi": "BBG000000001"},
            {"ticker": "ABC", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "UN", "figi": "BBG000000002"},
        ]
        result = select_ticker(matches, "US")
        self.assertEqual(result["status"], "unique_ticker")
        self.assertEqual(result["selected"]["ticker"], "ABC")
        self.assertEqual(result["selected"]["exchCode"], "US")

    def test_rejects_openfigi_security_description_codes_and_selects_real_ticker(self):
        matches = [
            {"ticker": "9666678D", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "US", "figi": "BBG000000001"},
            {"ticker": "GTES", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "UA", "figi": "BBG000000002"},
            {"ticker": "GTES", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "UN", "figi": "BBG000000003"},
        ]
        result = select_ticker(matches, "GB")
        self.assertEqual(result["status"], "unique_ticker")
        self.assertEqual(result["selected"]["ticker"], "GTES")
        self.assertEqual(result["candidate_tickers"], ["GTES"])

    def test_rejects_openfigi_security_description_when_no_real_ticker_exists(self):
        matches = [
            {"ticker": "9666655D", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "US", "figi": "BBG000000001"},
            {"ticker": "9666655D", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "UN", "figi": "BBG000000002"},
        ]
        result = select_ticker(matches, "US")
        self.assertEqual(result["status"], "no_ticker_match")
        self.assertIsNone(result["selected"])
        self.assertEqual(result["candidate_tickers"], [])

    def test_prefers_valid_us_listing_over_country_market_code(self):
        matches = [
            {"ticker": "9666678D", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "US", "figi": "BBG000000001"},
            {"ticker": "GTES", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "UN", "figi": "BBG000000002"},
            {"ticker": "GTES", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "UA", "figi": "BBG000000003"},
            {"ticker": "1JL", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "GB", "figi": "BBG000000004"},
        ]
        result = select_ticker(matches, "GB")
        self.assertEqual(result["status"], "unique_ticker")
        self.assertEqual(result["selected"]["ticker"], "GTES")
        self.assertIn(result["selected"]["exchCode"], {"UN", "UA"})

    def test_prefers_exact_us_composite_and_excludes_when_issued_symbols(self):
        matches = [
            {"ticker": "BALL", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "US", "name": "BALL CORP"},
            {"ticker": "BLL", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "UI", "name": "BALL CORP"},
            {"ticker": "JNJ", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "US", "name": "JOHNSON & JOHNSON"},
            {"ticker": "JNJ/WD", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "US", "name": "JOHNSON & JOHNSON-W/D"},
        ]
        ball = select_ticker(matches[:2], "US")
        jnj = select_ticker(matches[2:], "US")
        self.assertEqual(ball["status"], "unique_ticker")
        self.assertEqual(ball["selected"]["ticker"], "BALL")
        self.assertEqual(jnj["status"], "unique_ticker")
        self.assertEqual(jnj["selected"]["ticker"], "JNJ")

    def test_uses_clean_base_ticker_from_otc_composite(self):
        matches = [
            {"ticker": "9666655D", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "US"},
            {"ticker": "XOM", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "EO"},
            {"ticker": "XOMEUR", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "EO"},
            {"ticker": "XOMGBX", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "EO"},
        ]
        result = select_ticker(matches, "US")
        self.assertEqual(result["status"], "unique_ticker")
        self.assertEqual(result["selected"]["ticker"], "XOM")

    def test_does_not_select_unverified_non_us_local_ticker(self):
        matches = [
            {"ticker": "1JL", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "GB"},
        ]
        result = select_ticker(matches, "GB")
        self.assertEqual(result["status"], "no_ticker_match")

    def test_distinct_ticker_candidates_remain_ambiguous(self):
        matches = [
            {"ticker": "ABC", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "US"},
            {"ticker": "XYZ", "marketSector": "Equity", "securityType2": "Common Stock",
             "exchCode": "US"},
        ]
        result = select_ticker(matches, "US")
        self.assertEqual(result["status"], "ambiguous_ticker")
        self.assertIsNone(result["selected"])
        self.assertEqual(result["candidate_tickers"], ["ABC", "XYZ"])

    def test_options_and_warrants_are_not_selected_as_equity(self):
        matches = [
            {"ticker": "ABC1", "marketSector": "Equity", "securityType2": "Option",
             "exchCode": "US"},
            {"ticker": "ABC2", "marketSector": "Equity", "securityType2": "Warrant",
             "exchCode": "US"},
        ]
        result = select_ticker(matches, "US")
        self.assertEqual(result["status"], "no_ticker_match")


    def test_starting_universe_includes_funds_and_benchmark_proxies(self):
        base = {
            "report_date": "2025-06-30", "is_common_equity": "True",
            "pct_net_assets": "5.0", "isin": "US0378331005",
            "cusip": "037833100", "ticker": "", "name": "Apple Inc.",
            "investment_country": "US",
        }
        holdings = pd.DataFrame([
            {**base, "entity": "Fund A", "role": "fund"},
            {**base, "entity": "SPY", "role": "benchmark_sp500"},
            {**base, "entity": "IWB", "role": "benchmark_russell1000"},
        ])
        universe, start = build_security_universe(holdings)
        self.assertEqual(len(universe), 1, "same security should be mapped once")
        self.assertEqual(universe[0]["entity_count"], 3)
        self.assertEqual(universe[0]["fund_count"], 1)
        self.assertEqual(set(universe[0]["roles"].split("|")),
                         {"fund", "benchmark_sp500", "benchmark_russell1000"})
        self.assertEqual(set(start["entity"]), {"Fund A", "SPY", "IWB"})

    def test_non_starting_date_and_non_equity_rows_are_excluded(self):
        rows = []
        for date, equity, entity in [
            ("2025-06-30", "True", "Fund A"),
            ("2025-09-30", "True", "Fund B"),
            ("2025-06-30", "False", "Fund C"),
        ]:
            rows.append({
                "entity": entity, "role": "fund", "report_date": date,
                "is_common_equity": equity, "pct_net_assets": "5.0",
                "isin": "US0378331005", "cusip": "037833100",
                "ticker": "", "name": "Apple Inc.", "investment_country": "US",
            })
        universe, start = build_security_universe(pd.DataFrame(rows))
        self.assertEqual(len(universe), 1)
        self.assertEqual(set(start["entity"]), {"Fund A"})


if __name__ == "__main__":
    unittest.main()
