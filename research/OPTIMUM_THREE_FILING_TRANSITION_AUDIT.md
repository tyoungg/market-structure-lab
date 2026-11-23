# Optimum Large Cap Growth: Three-Filing Holdings and Sub-Adviser Allocation Review

**Review date:** 2026-11-23  
**N-PORT filing dates:** 2025-06-30, 2025-09-30, 2025-12-31  
**Advisory-agreement effective date:** 2025-12-01  
**Source holdings:** validated C.2 N-PORT cohort, GitHub Actions run #21, commit b4b5ade454d5900241b8b66dd3a6a05b400c09a2.

## Executive conclusion

The evidence supports an ownership/control and advisory-agreement transition, not a change in the named investment manager from Delaware Management Company (DMC) to Nomura. DMC remained the named investment manager; following Nomura's acquisition of the relevant Macquarie public asset-management business, DMC became a series of Nomura Investment Management Business Trust. The prior advisory agreement automatically terminated and a new DMC agreement became effective December 1, 2025.

American Century and Los Angeles Capital continued as sub-advisers under new agreements. Official monthly allocation disclosures show a nearly unchanged aggregate split between those sub-advisers across the transition. This supports continuity in the disclosed allocation structure, but does not establish unchanged security-level sleeve holdings, personnel, processes, or day-to-day decisions.

## Three N-PORT snapshots

Weights are normalized to each date's common-equity sleeve.

| Filing date | Common-equity positions | Equity sleeve (% NAV) | Top 5 (% equity) | Top 10 (% equity) | Top 20 (% equity) |
|---|---:|---:|---:|---:|---:|
| 2025-06-30 | 126 | 99.50 | 41.94 | 57.99 | 71.23 |
| 2025-09-30 | 117 | 99.83 | 42.89 | 59.29 | 71.69 |
| 2025-12-31 | 118 | 99.96 | 42.07 | 58.33 | 70.74 |

| Interval | Continuing securities | Added at later snapshot | Absent at later snapshot | One-way composition distance (pp) |
|---|---:|---:|---:|---:|
| June 30 → September 30 | 97 | 20 | 29 | 16.93 |
| September 30 → December 31 | 89 | 29 | 28 | 14.56 |

The one-way composition distance is one-half the sum of absolute changes in normalized security weights. It is not turnover: prices, flows, corporate actions, and other events can change weights without trades. "Added" and "absent" mean only present or absent at the two filing dates. The September-to-December interval has less aggregate endpoint weight movement than June-to-September; concentration does not show a clear December reset.

### Largest September-to-December weight changes

| Security | September weight (% equity) | December weight (% equity) | Change (pp) |
|---|---:|---:|---:|
| Meta Platforms | 4.31 | 3.04 | -1.27 |
| Gilead Sciences | 0.92 | 0.06 | -0.86 |
| Phillips 66 | 0.12 | 0.95 | +0.83 |
| Netflix | 3.44 | 2.65 | -0.78 |
| HEICO | 0.85 | 0.12 | -0.73 |
| Lam Research | 0.16 | 0.82 | +0.66 |
| Alphabet (GOOGL) | 3.50 | 4.11 | +0.61 |
| Bank of America | 0.00 | 0.59 | +0.59 |
| NVIDIA | 14.21 | 13.64 | -0.57 |
| Vertex Pharmaceuticals | 0.00 | 0.56 | +0.56 |
| Spotify | 0.00 | 0.56 | +0.56 |
| Broadcom | 3.25 | 3.77 | +0.52 |

## Official monthly sub-adviser allocations

The official Optimum fund page reports allocations including securities, cash, and other assets managed by each sub-adviser in its sleeve.

| Month-end | American Century | DMC sub-adviser sleeve | Los Angeles Capital |
|---|---:|---:|---:|
| 2025-08-31 | 48.87% | 0.00% | 51.13% |
| 2025-09-30 | 48.51% | 0.00% | 51.49% |
| 2025-10-31 | 48.79% | 0.00% | 51.21% |
| 2025-11-30 | 48.65% | 0.00% | 51.35% |
| 2025-12-31 | 48.44% | 0.00% | 51.56% |

September 30 to December 31: American Century -0.07 percentage points; Los Angeles Capital +0.07 points. DMC's 0.00% refers to its sub-adviser sleeve allocation, not its role as investment manager.

## Dated portfolio-manager roster and responsibility comparison

The March 31, 2025 prospectus/SAI disclosure (pre-transition) and the March 31, 2026 prospectus/SAI disclosure (post-transition) list the same six portfolio managers for the two Optimum Large Cap Growth Fund sub-adviser sleeves. All six retain the same stated fund start dates. The filings continue to assign day-to-day management of each sleeve to the respective sub-adviser teams.

| Sub-adviser | Portfolio manager | 2025 title | 2026 title | Fund start | Comparison |
|---|---|---|---|---|---|
| American Century | Keith Lee, CFA | SVP; Senior PM; Co-CIO, Global Growth Equity | Same | July 2022 | Unchanged |
| American Century | Jeff Bourke, CFA | VP; Portfolio Manager | VP; Senior Portfolio Manager | July 2022 | Title updated; same manager |
| American Century | Tong Li | Portfolio Manager; Senior Quantitative Analyst | Same | July 2024 | Unchanged |
| Los Angeles Capital | Hal W. Reynolds, CFA | Vice Chair; Senior Portfolio Manager | Same | January 2023 | Unchanged |
| Los Angeles Capital | Daniel Arche, CFA | Director, Portfolio Strategy; Senior Portfolio Manager | Same | January 2023 | Unchanged |
| Los Angeles Capital | Daniel E. Allen, CFA | CEO; Senior Portfolio Manager | Same | January 2023 | Unchanged |

The responsibility descriptions also remain materially consistent. American Century's three named managers are described as primarily responsible for day-to-day management of its portion. Los Angeles Capital's three named managers are described as primarily responsible for its portion; the filing continues to describe Reynolds as overseeing the investment process, Arche as managing accounts under the firm's process and risk parameters, and Allen as a senior Portfolio Management team member and Investment Committee member.

The manager-level governance description remains consistent in substance: DMC has overall responsibility for general management, including selecting sub-advisers and monitoring their investment activity. The legal entity's trust affiliation changes from Macquarie Investment Management Business Trust to Nomura Investment Management Business Trust, but DMC remains the named investment manager.

**Interpretation:** this is positive documentary evidence of continuity in the disclosed sub-adviser portfolio-manager roster and stated role allocation across the transition. It is not proof that there were no temporary or unreported personnel changes, that actual responsibilities were performed identically, or that security-level decisions and trading processes were unchanged. The SAI's other-accounts tables are firm/manager-level snapshots with changed account counts and assets; they do not identify Optimum-specific decisions and should not be treated as direct evidence of continuity or discontinuity.

The formal flag therefore remains **day-to-day portfolio management change: not established**. A roster match is evidence about named personnel and disclosed responsibilities, not a substitute for trade-level or internal process records.

Reproducible row-level comparison: `research/OPTIMUM_PORTFOLIO_MANAGER_ROSTER_COMPARISON_2025_2026.csv`.

Sources:
- [Pre-transition prospectus/SAI, dated July 31, 2025; manager and portfolio-manager disclosures](https://www.sec.gov/Archives/edgar/data/1227523/000114544325000218/oft-20250331.htm)
- [Post-transition prospectus/SAI, dated July 31, 2026; manager and portfolio-manager disclosures](https://www.sec.gov/Archives/edgar/data/1227523/000113322826010974/noft-efp26595_485bpos.htm)

## What the filings cannot establish

- Which sub-adviser managed any particular security.
- Trade dates, quantities bought or sold, or who made the investment decision.
- Whether observed changes reflect trades, price movements, flows, corporate actions, or other effects.
- Whether the acquisition or new advisory agreement caused any holdings change.
- Whether day-to-day portfolio management changed or remained unchanged.
- December 31 is a month-end snapshot 30 days after the effective date, not a daily record of the transition period.

## Sources and reproducibility

- SEC definitive information statement (December 9, 2025): https://www.sec.gov/Archives/edgar/data/1227523/000207184425000626/optimum12092025def14c.htm. It identifies DMC as manager, describes the acquisition, automatic termination of the prior agreement, new agreement effective date, and continuation of both sub-advisers.
- Official Optimum fund page and allocation history: https://www.optimummutualfunds.com/products/optimum-large-cap-growth-fund. Allocation history retrieved 2026-11-23; the page notes that allocations include securities, cash, and other assets managed by each sub-adviser in its sleeve.
- Input holdings: nport_cohort_common_equity.csv from C.2 workflow run #21.
- Official allocation snapshot: research/OPTIMUM_SUBADVISER_ALLOCATIONS_2025.csv.
- Regeneration script: scripts/audit_optimum_manager_transition.py.
