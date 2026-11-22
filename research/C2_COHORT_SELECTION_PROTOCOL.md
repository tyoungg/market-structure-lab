# C.2 Multi-Fund Cohort Selection and Acquisition Protocol

**Branch:** `RUSSEL_SP`  
**Status:** Candidate cohort predeclared; SEC holdings acquisition audit pending  
**Holdings dates:** 2025-06-30, 2025-09-30, and 2025-12-31  
**Funds:** Six active-management candidates, provisionally grouped into growth, value, and blend buckets  
**Benchmarks:** SPY and IWB N-PORT holdings proxies

## 1. Purpose

The single-fund Optimum Large Cap Growth pilot established that SEC N-PORT holdings, security identifiers, adjusted-price returns, and the no-trade Active Share decomposition can be joined reproducibly. The next test is whether the same pipeline works across multiple managers and style buckets.

This cohort is a **purposive feasibility sample**, not a random or representative sample of the active-fund universe. It is not intended to support population-wide inference.

## 2. Predeclared cohort

| Fund | SEC CIK | Series ID | Provisional style bucket | Selection rationale |
|---|---|---|---|---|
| Optimum Large Cap Growth Fund | 0001227523 | S000002422 | Growth | Existing C.1-linked pilot fund; large-cap growth mandate |
| Fidelity Contrafund | 0000024238 | S000006037 | Growth | Large diversified active growth-oriented fund |
| JPMorgan Large Cap Growth Fund | 0000763852 | S000003856 | Growth | Explicit large-cap growth mandate |
| JPMorgan Large Cap Value Fund | 0000763852 | S000003857 | Value | Explicit large-cap value mandate |
| Fidelity Magellan Fund | 0000061397 | S000007112 | Blend | Diversified active capital-appreciation mandate |
| Oakmark Fund | 0000872323 | S000002758 | Value | Active value-oriented large-company fund |

The style buckets are manual research groupings based on stated fund objectives and strategy descriptions. They are not Morningstar style-box classifications and remain provisional until the strategy-evidence review is complete.

## 3. Strategy evidence references

These are the starting references for manual strategy review. A prospectus dated after a holdings date may corroborate a strategy, but it must not be treated as contemporaneous evidence without checking for intervening changes.

- Optimum Large Cap Growth Fund: [2025 semiannual shareholder report](https://www.sec.gov/Archives/edgar/data/1227523/000119312525298790/d947723dncsrs.htm), which reports the Russell 1000 Growth benchmark, holdings, and portfolio turnover.
- Fidelity Contrafund: [March 1, 2025 summary prospectus](https://www.sec.gov/Archives/edgar/data/24238/000002423825000021/filing8433.htm).
- JPMorgan Large Cap Growth Fund: [January 31, 2025 summary prospectus](https://www.sec.gov/Archives/edgar/data/763852/000119312525018386/d925205d497k.htm).
- JPMorgan Large Cap Value Fund: [November 1, 2025 summary prospectus](https://www.sec.gov/Archives/edgar/data/763852/000119312525260189/d183430d497k.htm). This is after the holdings dates and is corroborative only until an earlier 2025 prospectus is located.
- Fidelity Magellan Fund: [May 30, 2025 summary prospectus](https://www.sec.gov/Archives/edgar/data/61397/000006139725000066/filing8713.htm).
- Oakmark Fund: [January 28, 2025 summary prospectus, amended May 19, 2025](https://www.sec.gov/Archives/edgar/data/872323/000110465925050333/tm2514028d4_497k.htm).

**Important:** no multi-fund Active Share or no-trade drift conclusion is authorized until each fund's strategy is reviewed and any mandate/strategy change during the sample period is checked. The acquisition run itself is only a data/identity feasibility test.

## 4. Frozen holdings manifest

The exact 24 filing records—six funds and two benchmark proxies, each at all three dates—are frozen in [`C2_COHORT_MANIFEST.csv`](C2_COHORT_MANIFEST.csv). The manifest records the expected registrant CIK, series ID, series name, accession, report date, and primary XML URL.

The acquisition workflow must validate:

1. All 16 XML downloads succeed.
2. Every `repPdDate` equals the manifest report date.
3. Every fund series ID and series name match the manifest.
4. SPY's UIT identity is validated through its SEC accession path CIK and filing-index identity; its N-PORT XML may report `N/A` in series/registrant name fields.
5. SPY and IWB are both present at both dates.
6. All positions, identifiers, market values, and reported percentages are retained, including positions that cannot yet be mapped to a ticker.

## 5. Identifier normalization and mapping

The acquisition parser now treats `N/A`, `NA`, `NONE`, `XXXX`, and `000000000` as missing normalized identifiers while preserving their original values in `cusip_raw`, `isin_raw`, and `ticker_raw`. Coverage metrics are calculated only from valid normalized identifiers.

For security matching, use **ISIN first, then CUSIP, then a verified N-PORT ticker, then a normalized-name fallback**. The cohort shows higher value-weight ISIN coverage than CUSIP coverage, especially for IWB and several active funds. The single-fund pilot will be rerun under this same priority so the reported results are comparable.

Ticker mapping will use the public [OpenFIGI v3 Mapping API](https://www.openfigi.com/api/documentation). The API maps third-party identifiers such as ISIN and CUSIP to FIGI records and ticker/exchange metadata. The unauthenticated limit is 25 requests per minute and 10 mapping jobs per request. The mapping request will set `includeUnlistedEquities=true` so delisted securities are not excluded by default. All candidate matches are retained; ambiguous ticker/exchange mappings are not auto-resolved.

The mapping audit will produce a security-level map and per-fund starting-equity-value coverage. Only after the mapping output and manual ambiguity review pass the 95% price-coverage gate will the multi-fund no-trade calculation proceed.

## 6. Acquisition and mapping outputs

The first cohort run produces:

- all-position CSV;
- common-equity CSV;
- per-report manifest/quality metrics;
- original SEC XML files in the workflow artifact only;
- a report of holdings counts, common-equity weights, CUSIP/ISIN/ticker coverage, and duplicate identifiers.

Raw SEC XML files are not committed to the repository.

## 7. Gates before multi-fund drift calculation

Do not calculate pooled cohort results until:

- all 24 N-PORT filings pass date and identity validation;
- all six candidate funds have reviewed strategy evidence and provisional style buckets are confirmed or corrected;
- common-equity holdings reconcile to reported values;
- duplicate CUSIPs are aggregated;
- security identifier and price coverage is reported fund by fund;
- the same SPY/IWB benchmark definitions and report dates are applied to every fund;
- any fund failing the 95% starting-equity price-coverage gate is withheld individually rather than silently imputed.

The same equity-only Active Share formula, no-trade total-return drift, ordered decomposition, and unpriced-position sensitivity used in the single-fund pilot will be applied to each eligible fund. The actual-portfolio-change component remains descriptive, not a causal estimate of manager trading or turnover.

## 8. Interpretation limits

- Six purposively selected funds do not represent the active-fund population.
- Growth/value/blend buckets are descriptive controls, not a formal style taxonomy.
- SPY and IWB are ETF holdings proxies, not official index constituent/weight files.
- Yahoo Finance adjusted prices remain an exploratory public price source.
- This 2025 cohort remains separate from the historical 1979–2023 TR/CRSP panel until a valid fund/provider bridge is established.


## 9. Second-quarter transition pre-registration

The extension adds the 2025-12-31 filings for the same eight entities. The next calculation is explicitly the 2025-09-30 to 2025-12-31 transition; it does not reselect funds, alter benchmark proxies, or pool the two quarterly transitions before examining each separately. The mapping universe is constructed from 2025-09-30 common-equity holdings only, and all price returns use exact 2025-09-30 and 2025-12-31 adjusted-close endpoints. Each entity retains its own 95% mapping and price coverage gates. Missing or ambiguous mappings remain unresolved rather than being filled by ticker guesses.
