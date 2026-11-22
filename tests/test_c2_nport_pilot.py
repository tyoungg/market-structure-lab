import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_c2_nport_pilot import parse_nport_xml, validate_identity, summarize, position_identifiers


class NportPilotTests(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "entity": "Sample Active Fund", "role": "fund", "report_date": "2025-06-30",
            "cik": "0000000001", "series_id": "S000000001", "series_name": "Sample Active Fund",
            "accession": "0000000001-25-000001", "url": "https://www.sec.gov/Archives/edgar/data/1/000000000125000001/primary_doc.xml",
        }
        self.xml = b"""<?xml version="1.0"?>
        <edgarSubmission xmlns="http://www.sec.gov/edgar/nport">
          <formData>
            <genInfo>
              <regCik>0000000001</regCik>
              <regName>Sample Registrant</regName>
              <seriesId>S000000001</seriesId>
              <seriesName>Sample Active Fund</seriesName>
              <repPdDate>2025-06-30</repPdDate>
            </genInfo>
            <fundInfo><netAssets>100000000</netAssets><totAssets>101000000</totAssets><totLiabs>1000000</totLiabs></fundInfo>
            <invstOrSecs>
              <invstOrSec>
                <name>Sample Corporation</name><title>Common Stock</title><cusip>123456789</cusip>
                <identifiers><isin value="US1234567890"/><other otherDesc="Ticker" value="SAMP"/></identifiers>
                <balance>1000</balance><units>NS</units><curCd>USD</curCd>
                <valUSD>5000000</valUSD><pctVal>5.0</pctVal><payoffProfile>Long</payoffProfile><assetCat>EC</assetCat>
              </invstOrSec>
              <invstOrSec>
                <name>Cash</name><title>Cash</title><cusip>N/A</cusip>
                <balance>1000000</balance><units>NS</units><curCd>USD</curCd>
                <valUSD>1000000</valUSD><pctVal>1.0</pctVal><payoffProfile>N/A</payoffProfile><assetCat>STIV</assetCat>
              </invstOrSec>
            </invstOrSecs>
          </formData>
        </edgarSubmission>"""

    def test_parse_and_validate_identity(self):
        meta, positions = parse_nport_xml(self.xml, self.spec)
        validate_identity(meta, self.spec)
        self.assertEqual(meta["rep_pd_date"], "2025-06-30")
        self.assertEqual(meta["xml_series_id"], "S000000001")
        self.assertEqual(meta["net_assets_usd"], 100000000.0)
        self.assertEqual(len(positions), 2)
        self.assertTrue(positions[0]["is_common_equity"])
        self.assertEqual(positions[0]["cusip"], "123456789")
        self.assertEqual(positions[0]["ticker"], "SAMP")

    def test_report_date_mismatch_fails_closed(self):
        meta, _ = parse_nport_xml(self.xml, self.spec)
        bad = dict(self.spec, report_date="2025-09-30")
        with self.assertRaises(ValueError):
            validate_identity(meta, bad)

    def test_series_id_mismatch_fails_closed(self):
        meta, _ = parse_nport_xml(self.xml, self.spec)
        bad = dict(self.spec, series_id="S000000999")
        with self.assertRaises(ValueError):
            validate_identity(meta, bad)

    def test_spy_uit_n_a_xml_name_uses_sec_accession_identity(self):
        xml = b"""<edgarSubmission xmlns="http://www.sec.gov/edgar/nport">
          <formData><genInfo><regCik>N/A</regCik><regName>N/A</regName>
          <seriesId>N/A</seriesId><seriesName>N/A</seriesName><repPdDate>2025-06-30</repPdDate></genInfo>
          <fundInfo><netAssets>1000000</netAssets></fundInfo></formData></edgarSubmission>"""
        spec = {
            "entity":"SPY","role":"benchmark_sp500","report_date":"2025-06-30",
            "cik":"0000884394","series_id":"","series_name":"SPDR S&P 500 ETF Trust",
            "accession":"0001752724-25-211156",
            "url":"https://www.sec.gov/Archives/edgar/data/884394/000175272425211156/primary_doc.xml"
        }
        meta, _ = parse_nport_xml(xml, spec)
        validate_identity(meta, spec)
        self.assertIn("SEC accession path CIK", meta["identity_validation_method"])

    def test_summary_reports_identifier_coverage(self):
        meta, positions = parse_nport_xml(self.xml, self.spec)
        summary = summarize(meta, positions, 1234, "abc")
        self.assertEqual(summary["equity_position_count"], 1)
        self.assertEqual(summary["equity_weight_pct_net_assets"], 5.0)
        self.assertEqual(summary["equity_ticker_coverage_pct_of_equity"], 100.0)
        self.assertEqual(summary["equity_cusip_coverage_pct_of_equity"], 100.0)
        self.assertEqual(summary["all_position_pct_net_assets"], 6.0)

    def test_na_identifiers_are_missing_but_raw_values_are_retained(self):
        node = ET.fromstring(
            b"<invstOrSec><cusip>000000000</cusip><identifiers>"
            b"<isin value='N/A'/><other otherDesc='Ticker' value='N/A'/>"
            b"</identifiers></invstOrSec>"
        )
        cusip, isin, ticker, other_json, cusip_raw, isin_raw, ticker_raw = position_identifiers(node)
        self.assertEqual((cusip, isin, ticker), ("", "", ""))
        self.assertEqual((cusip_raw, isin_raw, ticker_raw), ("000000000", "N/A", "N/A"))


if __name__ == "__main__":
    unittest.main()
