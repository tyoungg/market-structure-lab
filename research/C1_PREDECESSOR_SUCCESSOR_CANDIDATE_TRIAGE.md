# C.1 Predecessor/Successor Candidate Triage — First Pass

**Branch:** \`RUSSEL_SP\`  
**Screen reviewed:** 64 fundnos whose first unique-series match occurs in 2007–2009 after one or more earlier no-strict-candidate years.  
**Purpose:** Separate actual predecessor/successor events from same-series renames, strategy changes, and unrelated transactions within the same fund complex. This is a targeted triage, not a complete review of all 64.

## Findings

### 1. Legg Mason Small Cap Growth — confirmed multi-predecessor transaction; fundno linkage pending

The 2007 SEC filings document a complex identity transition:

- The target Legg Mason Partners Small Cap Growth Fund (CIK 355747) disclosed that it would be reorganized into Legg Mason Partners Small Cap Growth Fund I, with an expected effective date of March 2, 2007. The target's prospectus describes an actively selected small-cap growth portfolio.
- The December 31, 2007 annual report for the surviving Legg Mason Partners Small Cap Growth Fund says that before March 2, 2007 it was known as Legg Mason Partners Small Cap Growth Fund I.
- That surviving fund acquired both Legg Mason Partners Small Cap Growth Fund and Legg Mason Partners Small Cap Growth Opportunities Fund on March 2, 2007.
- The same annual report says that before April 16, 2007, the surviving fund was a series of Legg Mason Partners Series Funds, Inc.; it then became a series of Legg Mason Partners Equity Trust.
- Later SEC reports identify the same continuing portfolio as Legg Mason ClearBridge Small Cap Growth Fund and then ClearBridge Small Cap Growth Fund.

This is not a simple name change: two portfolios were absorbed by a surviving fund, and the surviving fund also moved between registrants. The screen flags fundno \`29224\`, with eight earlier years before its first unique-series match in 2007 and later series names including Legg Mason Partners Small Cap Growth Fund II and Legg Mason ClearBridge Small Cap Growth Fund.

**Disposition:** high-priority, documented predecessor/successor candidate. Do not add the eight earlier fund-years yet. The corporate event is proven, but the available screen does not identify which of the two predecessor series, or the surviving Fund I series, generated each Thomson Reuters quarterly observation. The next proof step is to map fundno 29224's quarter-level names/tickers and dates against the SEC predecessor and successor filing headers and the reorganization record. The transition also creates a risk of duplicate holdings if both predecessors and the successor are represented separately in the same quarter.

Sources:
- [January 26, 2007 target prospectus and merger notice, CIK 355747](https://www.sec.gov/Archives/edgar/data/355747/000119312507014355/d485bpos.htm)
- [December 31, 2007 survivor annual report, CIK 880366](https://www.sec.gov/Archives/edgar/data/880366/000119312508048871/dncsr.htm)
- [2012 annual report confirming later ClearBridge name and continuity of objective/strategy](https://www.sec.gov/Archives/edgar/data/880366/000119312512515929/d439271dncsr.htm)

### 2. Morgan Stanley Focus Growth — real merger, but not yet evidence of missing predecessor years for fundno 15501

SEC filings establish that Morgan Stanley Focus Growth Fund absorbed Morgan Stanley Growth Fund on October 20, 2006. Focus Growth itself had commenced operations in 1980 and was renamed from Morgan Stanley American Opportunities Fund effective July 3, 2006. The 64-row screen flags fundno \`15501\` as Morgan Stanley Focus Growth Fund, with earlier no-strict years beginning in 1987.

The key distinction is that the Morgan Stanley Growth Fund was the acquired portfolio, whereas Focus Growth was the surviving fund. The pre-2007 history attached to fundno 15501 may simply be the continuing Focus Growth/American Opportunities series whose historical SEC linkage was missed; it cannot be assumed to be the acquired Growth Fund. The merger is not enough to add the Growth Fund's observations to fundno 15501.

**Disposition:** documented corporate merger; no additional fund-years promoted. Require Thomson Reuters predecessor/successor fund-number mapping and SEC series-header reconciliation before recovery.

Sources:
- [Morgan Stanley Focus Growth Item 77M merger record, consummated October 20, 2006](https://www.sec.gov/Archives/edgar/data/314366/000132535807000132/focus77m.htm)
- [SEC prospectus supplement documenting the July 3, 2006 name change from American Opportunities](https://www.sec.gov/Archives/edgar/data/314366/000095013606004995/file1.htm)

### 3. Sentinel Sustainable Growth Opportunities — same-series name change, not a predecessor recovery

Sentinel Sustainable Emerging Companies Fund changed its name to Sentinel Sustainable Growth Opportunities Fund effective December 18, 2008. The corporation's articles of amendment explicitly amend the name of the same series. The annual report also describes the name and portfolio-management-team change.

**Disposition:** exclude from predecessor/successor recovery. Keep the name and manager transition in the strategy/management-event history; it does not create an additional legal portfolio lineage.

Sources:
- [Articles of amendment dated December 17, 2008](https://www.sec.gov/Archives/edgar/data/225843/000022584309000028/a22articlesofamendment.htm)
- [Sentinel annual report describing the December 18 name and manager change](https://www.sec.gov/Archives/edgar/data/225843/000022584309000020/ncsr1130.htm)

### 4. Eaton Vance Dividend Builder — same-series name and mandate change

Eaton Vance Utilities Fund changed its name to Eaton Vance Dividend Builder Fund effective August 15, 2007. The supplement also broadened the 80% investment policy from utility-company equities to dividend-paying common stocks and related convertible securities, while retaining at least 25% in utilities.

**Disposition:** exclude from predecessor/successor recovery. This is a same-fund strategy change, which matters for point-in-time style classification, but not a missing predecessor series.

Sources:
- [August 15, 2007 prospectus supplement](https://www.sec.gov/Archives/edgar/data/31266/000094039407000638/sit497supp.htm)
- [2007 N-CSR discussion of the same changes](https://www.sec.gov/Archives/edgar/data/31266/000110465907065573/a07-18205_1ncsrs.htm)

### 5. Evergreen Large Cap Equity / Enhanced S&P 500 — same-series name and strategy change

Effective September 30, 2007, Evergreen Large Cap Equity Fund changed its name to Evergreen Enhanced S&P 500 Fund. The supplement changed its objective to seek total return above the S&P 500 and specified a portfolio investing at least 80% in S&P 500 constituents, with a quantitative selection approach intended to outperform the index.

**Disposition:** not a predecessor/successor recovery. It is a material investment-strategy change that should be treated as a separate point-in-time style event in any active/enhanced-index classification. Do not assume the pre- and post-change observations represent an unchanged mandate.

Source:
- [July 13, 2007 prospectus supplement](https://www.sec.gov/Archives/edgar/data/1046026/000090724407000506/largecapequitysupp.htm)

## Triage scorecard

| Screen candidate | Corporate event found? | Event type | Fund-year recovery now supported? |
|---|---|---|---|
| 29224 — Legg Mason Small Cap Growth | Yes | Two predecessor portfolios absorbed; survivor later transferred between registrants | No; fundno-to-series quarter mapping pending |
| 15501 — Morgan Stanley Focus Growth | Yes | Growth Fund absorbed by Focus Growth | No; earlier fundno history may be continuing Focus Growth, not acquired Growth |
| 11304 — Sentinel Sustainable Growth Opportunities | Yes | Same-series name and manager change | No; not a predecessor event |
| 18680 — Eaton Vance Dividend Builder | Yes | Same-series name and investment-policy change | No; not a predecessor event |
| 3519 — Evergreen Enhanced S&P 500 | Yes | Same-series name and strategy change | No; not a predecessor event |

This five-case review does not estimate the prevalence of true predecessor/successor events across the remaining 59 candidates. It does demonstrate why the 64-row mechanical screen cannot be counted as 64 mergers.

## Next bounded step

Prioritize fundno 29224 for a quarter-level identity reconstruction. Resolve, in order:

1. Every fund name and ticker associated with fundno 29224 in each available quarterly observation.
2. The predecessor SEC series/class IDs and the surviving series ID(s), using pre- and post-event filing headers rather than the 2010 registry alone.
3. The March 2, 2007 merger date and April 16, 2007 registrant-transfer date against each observation date.
4. Whether the two acquired portfolios have separate Thomson Reuters fundnos elsewhere in the panel; prevent duplicate holdings and double-counting.
5. Only then determine which pre-2007 fund-years can be recovered as active lineage observations.

Until this mapping is completed, retain the original 30 adjudications as the canonical active seed and keep the Everest/Calvert two-row recovery and Legg Mason candidate outside the canonical ledger. C.1 remains no-go for population-level inference.
