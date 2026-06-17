# Market Structure Lab

A Streamlit-based research tool for analyzing index inclusion events and their impact on stock performance.

## Overview

The Market Structure Lab provides a suite of tools to test the thesis that market structure and passive flows create systematic performance deviations. By comparing stocks added to major indexes (like the S&P 500) against a counterfactual portfolio of "twin" stocks (matched by fundamentals), we can isolate the "inclusion effect" (Green Score).

## Features

- **Event Study**: Visualize individual stock performance vs. a benchmark around the inclusion date.
- **Twin Analysis**: Automatically find fundamentally similar stocks using K-Nearest Neighbors and build a counterfactual portfolio.
- **Aggregate Study**: Run the analysis over hundreds of historical events to find systematic alpha.
- **Data Manager**: Manage price caches and build fundamental universes for matching.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd market-structure-lab
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app:
```bash
streamlit run app.py
```

## Project Structure

- `app.py`: Main entry point.
- `pages/`: Streamlit page implementations.
- `utils/`: Core logic for data loading, matching, and analysis.
- `data/`: CSV and Parquet data files.
- `cache/`: Cached price history from Yahoo Finance.

## Core Methodology

The **Green Score** is calculated as:
`Green Score = Stock Return - Twin Portfolio Return`

An evolved score can also incorporate factors like valuation expansion, liquidity changes, and momentum persistence.
