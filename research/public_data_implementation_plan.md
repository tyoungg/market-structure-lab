# Public-data implementation plan

**Decision:** The no-trade counterfactual study will use publicly obtainable data only. No CRSP, WRDS, Bloomberg, FactSet, Morningstar Direct, or other paid market-data subscriptions.

## 1. Source hierarchy

| Need | Preferred public source | Role | Limitation |
|---|---|---|---|
| Fund holdings and assets | SEC Form N-PORT quarterly bulk datasets | Authoritative holdings observations | Quarterly public dissemination; as-filed data; amendments and extraction errors must be handled |
| Original filing validation | SEC EDGAR filing XML / filing index | Verify flattened archive records | More complex to parse at scale |
| Security identifiers | N-PORT CUSIP, ISIN, LEI, issuer/title/name, plus SEC and issuer filings | Build dated security crosswalk | Ticker and identifiers can be missing, changed, reused, or ambiguous |
| Security returns | Freely accessible adjusted price history, initially Yahoo Finance/yfinance as a *candidate* | Pilot-only total-return proxy using adjusted prices | Not a canonical open dataset; delisted coverage and historical identifier mapping are incomplete/uncertain |
| Corporate actions / delistings | SEC filings, issuer merger documents, exchange notices, public company announcements | Resolve specific events and terminal values | Manual/event-specific; unresolved cases remain flagged |
| Benchmark holdings | N-PORT filings for a low-cost S&P 500 index mutual fund or ETF | Same-date tracker-holdings proxy for benchmark weights | Not official S&P index weights; fund cash, expenses, sampling, and tracking differences remain |
| Historical membership cross-check | Public historical constituent/change records with source provenance | Check point-in-time membership | Community-maintained reconstructions are not official index data and do not supply official weights |

SEC bulk data page: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets  
SEC N-PORT readme: https://www.sec.gov/files/nport_readme.pdf

The SEC says N-PORT datasets cover October 2019 onward, are published quarterly, and contain only filings already disseminated. Fund reports contain monthly portfolio information, but the public bulk release is not a complete real-time monthly feed. The SEC also cautions that the flattened datasets are as-filed and may contain extraction inaccuracies; original filings remain the validation source.

## 2. Benchmark choice

Use the holdings of a publicly filing S&P 500 tracker as the primary benchmark-weight proxy for the first pilot. The 2026 Q3 archive includes Schwab S&P 500 Index Fund, which has a useful common-equity holdings schedule.

Rules:
- Call it the **S&P 500 tracker-fund proxy**, never “official S&P 500 weights.”
- Use the tracker filing's actual reported positions and NAV weights for the exact ending report date.
- Do not use current constituents or equal weights to backfill historical cap weights.
- Keep official index Active Share as a future extension only if a public, reproducible historical source for both membership and weights is established.
- Report tracker cash, derivatives, sampling, and any non-equity positions separately.

## 3. Security-return protocol

A free price feed is a feasibility source, not an automatic ground truth.

1. Resolve each N-PORT holding to a security using CUSIP/ISIN/LEI and issuer/security description. Ticker alone is insufficient.
2. Maintain a dated crosswalk with match method, evidence URL, confidence, and reviewer status.
3. Retrieve adjusted price histories only after validating that the symbol maps to the same security over the full interval.
4. Check splits and dividends against public corporate-action records for a sample and all material outliers.
5. For acquisitions, mergers, liquidations, spin-offs, and delistings, use public primary documents to identify the terminal security/cash consideration and effective date.
6. If the return cannot be established, mark the position as unresolved. Never silently delete it, assign zero return, or carry forward its last price.
7. Report coverage as a percentage of beginning NAV and common-equity weight, not merely a percentage of rows.

Yahoo Finance/yfinance is a candidate for the pilot because adjusted historical prices are freely accessible, but it is not an official SEC data source, its terms and availability can change, and its delisted-security history must be empirically tested. A successful download is not proof of a valid historical match.

## 4. Strict-sample rule

For each fund-quarter:
- Keep the full raw holdings universe and the full holdings/NAV reconciliation.
- Calculate no-trade weights only for positions with validated return treatment.
- Do not renormalize a partial set of matched holdings and present it as the whole fund.
- Set a minimum coverage threshold only after measuring pilot coverage. Freeze that threshold before scaling.
- Exclude low-coverage intervals from the strict estimate, but preserve them in the audit panel.
- Provide a sensitivity table showing the impact of unresolved positions and any defensible return bounds.

This means the first empirical result may cover fewer fund-quarters than the raw N-PORT panel. That is preferable to false precision.

## 5. Pilot sequence

1. Assemble all SEC quarterly archives from 2019 Q4 through the latest complete release. The uploaded 2026 Q3 ZIP is one quarterly release, not the full historical panel.
2. Resolve amendments and duplicate submissions across the combined archives, at the fund-series/report-date grain.
3. Select a small set of active large-cap mutual fund series with at least two consecutive observations, retaining dead/merged funds when filings exist.
4. Select a same-date S&P 500 tracker-fund filing as the benchmark proxy.
5. Build the security crosswalk for the pilot holdings and measure adjusted-price coverage.
6. Manually validate the largest unmatched positions and all material corporate-action cases.
7. Calculate one or two intervals end-to-end, including actual portfolio, no-trade portfolio, tracker-proxy Active Share, missing-return coverage, and NAV reconciliation.
8. Only scale if the strict-sample coverage and validation criteria pass.

## 6. What this design can and cannot establish

**Can establish, subject to coverage:** how much the holdings weights of observed active funds would have drifted under a no-trade assumption, and how the reported ending portfolios compare with that mechanical path and a public tracker-fund proxy.

**Cannot establish from this design alone:** manager intent, skill, causal trading effects, official S&P index Active Share, or comprehensive treatment of every delisted security. The signed actual-minus-no-trade Active Share difference remains descriptive and can also reflect flows, fund-level events, corporate actions, and data coverage.

## 7. Public-source references

- SEC Form N-PORT datasets and quarterly archive downloads: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
- SEC Form N-PORT readme and table definitions: https://www.sec.gov/files/nport_readme.pdf
- SEC EDGAR company and filing search: https://www.sec.gov/edgar/search/
- Public historical S&P 500 membership reconstruction example (community-maintained, not official): https://github.com/lawcal/sp500-components-history
