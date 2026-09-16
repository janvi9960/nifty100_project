# Nifty 100 Analytics Dashboard

## Project Overview

The **Nifty 100 Financial Intelligence Platform** is a comprehensive financial analytics project designed to analyze Nifty 100 companies using Python, SQLite, Streamlit, Plotly, NLP techniques, financial analytics, clustering, and REST APIs.

The platform transforms raw financial data into structured financial insights, company-level analytics, screening results, peer comparisons, valuation indicators, cash-flow intelligence, investment-style clusters, interactive dashboards, PDF reports, and API-accessible data.

The project covers **92 Nifty 100 companies** and uses financial data across multiple years.

---

## Project Objectives

The main objectives of the project are:

* Collect and organize financial data for Nifty 100 companies.
* Build a structured SQLite financial database.
* Perform financial statement analysis.
* Calculate and validate financial ratios.
* Analyze profitability, growth, leverage, and cash flow.
* Build company screening functionality.
* Perform peer-group comparisons.
* Analyze sectors and sector-level performance.
* Develop valuation indicators.
* Generate company-level pros and cons using NLP.
* Analyze cash-flow quality and capital allocation.
* Group companies into financial archetypes using clustering.
* Build an interactive Streamlit dashboard.
* Develop REST APIs using FastAPI.
* Generate automated PDF and Excel reports.
* Create automated tests and validate project acceptance criteria.

---

# Technologies Used

* **Python 3.14.4**
* **Pandas**
* **NumPy**
* **SQLite**
* **Scikit-learn**
* **Streamlit**
* **Plotly**
* **FastAPI**
* **Uvicorn**
* **Pytest**
* **OpenPyXL**
* **PyYAML**
* **Excel**
* **Git & GitHub**

---

# Project Structure

```text
nifty100_project/
│
├── data/
│   └── nifty100.db
│
├── output/
│   ├── valuation_summary.xlsx
│   ├── valuation_flags.csv
│   ├── cluster_labels.csv
│   ├── cluster_profile.csv
│   ├── outlier_report.csv
│   ├── portfolio_stats.csv
│   ├── analysis_parsed.csv
│   ├── pros_cons_generated.csv
│   ├── cashflow_intelligence.xlsx
│   ├── cashflow_kpis.xlsx
│   ├── cashflow_cfo_quality.csv
│   ├── cashflow_distress.csv
│   ├── openapi.json
│   └── Nifty100_API_Postman_Collection.json
│
├── reports/
│   ├── tearsheets/
│   ├── sector/
│   ├── screener/
│   ├── peer_group/
│   ├── portfolio/
│   ├── elbow_plot.png
│   └── correlation_heatmap.png
│
├── src/
│   ├── analytics/
│   ├── api/
│   ├── etl/
│   ├── nlp/
│   └── reports/
│
├── tests/
│   ├── api/
│   └── kpi/
│
├── README.md
└── .gitignore
```

---

# Sprint 1 — Data Ingestion & ETL

## Objective

Sprint 1 focused on building the foundation of the financial analytics platform by collecting, cleaning, normalizing, and storing financial data.

## Work Completed

* Collected financial data for Nifty 100 companies.
* Organized source Excel datasets.
* Developed the ETL pipeline.
* Implemented data loading into SQLite.
* Created structured database tables.
* Normalized company identifiers and financial fields.
* Handled different source-file formats.
* Added data validation and cleaning logic.
* Established the central `nifty100.db` database.

## Main Financial Data Areas

The project database contains structured information covering:

* Company information
* Sectors
* Profit & Loss
* Balance Sheet
* Cash Flow
* Financial Ratios
* Market capitalization
* Peer information
* Valuation-related information

## Database

The primary database is:

```text
data/nifty100.db
```

The project database contains financial data for **92 companies**.

Sprint 1 established the data foundation used by all later sprints.

---

# Sprint 2 — Financial Statement & Ratio Analysis

## Objective

Sprint 2 focused on converting raw financial statements into useful financial metrics and analytical indicators.

## Work Completed

### Profit & Loss Analysis

Financial statement data was structured and analyzed to support:

* Revenue analysis
* Profit analysis
* Operating performance
* Growth calculations
* Margin analysis

### Balance Sheet Analysis

The platform processes balance-sheet information for:

* Assets
* Liabilities
* Equity
* Debt
* Capital structure

### Financial Ratios

Financial ratios were calculated and validated for the Nifty 100 companies.

The analysis included metrics such as:

* Return on Equity
* Debt to Equity
* Profit margins
* Growth metrics
* Cash-flow related ratios
* Valuation ratios
* Quality indicators

### Ratio Validation

The ratio engine was tested across historical company data.

The Sprint 2 work resulted in a structured financial-ratio dataset that became the foundation for the screener, dashboard, valuation, and later intelligence modules.

---

# Sprint 3 — Company Screener & Peer Analysis

## Objective

Sprint 3 focused on enabling users to screen companies based on financial characteristics and compare companies against relevant peers.

## Company Screener

The screener supports multiple predefined investment-style presets.

The implemented presets include:

1. Quality Compounder
2. Value Pick
3. Growth Accelerator
4. Dividend Champion
5. Debt-Free Blue Chip
6. Turnaround Watch

The screener supports multiple financial metrics and can evaluate companies against defined criteria.

## Peer Analysis

Companies were grouped into peer groups based on sector/business characteristics.

The project created **11 peer groups**, including groups such as:

* IT Services
* Financial Services
* Consumer-related businesses
* Healthcare
* Energy
* Other relevant industry groups

The peer engine supports:

* Peer identification
* Peer comparison
* Metric comparison
* Percentile-based analysis
* Company-level benchmarking

## Output

The screener and peer engine became the foundation for:

* Dashboard screening
* Peer comparison
* Sector reports
* Company analysis
* API endpoints

---

# Sprint 4 — Streamlit Dashboard & Valuation

## Objective

Sprint 4 focused on converting the analytical results into an interactive financial dashboard and implementing valuation analysis.

## Streamlit Dashboard

An interactive Streamlit dashboard was developed using:

* Streamlit
* Plotly
* Pandas
* SQLite

The dashboard provides access to company and market-level financial analysis.

### Dashboard Areas

The dashboard includes functionality for:

* Home / overview
* Company analysis
* Financial health
* Screener
* Peer analysis
* Sector analysis
* Valuation
* Trends
* Company pros and cons
* Financial information

## Company Screening

The dashboard allows users to apply screening criteria and identify companies matching selected financial characteristics.

The screener supports all **92 companies** in the database.

## Sector Analysis

Sector-level analysis was implemented to compare companies and financial characteristics across sectors.

The project covers **10 broad sectors** containing the 92 companies.

## Valuation Analysis

Sprint 4 introduced valuation analysis using indicators including:

* P/E
* P/B
* EV/EBITDA
* Free Cash Flow Yield
* Historical P/E comparison
* Sector median comparison

The generated valuation file contains **92 company records**.

### Valuation Flags

The valuation analysis generated:

* Fair
* Discount
* Caution

The resulting valuation distribution was:

| Flag      | Companies |
| --------- | --------: |
| Fair      |        48 |
| Discount  |        30 |
| Caution   |        14 |
| **Total** |    **92** |

The valuation results were exported to:

```text
output/valuation_summary.xlsx
output/valuation_flags.csv
```

---

# Sprint 5 — Intelligence, NLP & Cash-Flow Analysis

## Objective

Sprint 5 expanded the project from traditional financial analysis into financial intelligence using NLP, cash-flow classification, capital allocation analysis, and automated reporting.

---

## NLP Financial Analysis

An NLP parser was developed to extract financial insights from structured analysis data.

### Parser Validation

The parser was improved from:

* 75 successfully parsed records / 5 failures

to:

* **80 successfully parsed records / 0 failures**

The parsed output is stored in:

```text
output/analysis_parsed.csv
```

## CAGR Validation

A validation process compared parsed CAGR values against the financial-ratio engine.

The validation contained:

* 30 comparisons
* 23 MATCH
* 6 NO_RATIO_VALUE
* 1 divergence above 5%

The divergence was identified and documented for further review.

---

## Automated Pros & Cons

A financial pros-and-cons generator was developed.

Results:

* **92 companies processed**
* **816 insights generated**
* 613 PRO insights
* 203 CON insights
* Mean confidence: **86.24**
* Confidence range: **60–98**
* Every company received at least one PRO and one CON insight.

Output:

```text
output/pros_cons_generated.csv
```

---

# Cash-Flow Intelligence

Sprint 5 introduced detailed cash-flow intelligence.

The system analyzes:

* CFO quality
* CapEx intensity
* Free Cash Flow
* FCF conversion
* FCF CAGR
* Deleveraging
* Distress conditions
* Capital allocation

## Capital Allocation Classification

The implemented classifications included:

* Shareholder Returns
* Reinvestor
* Mixed
* Growth Funded by Debt
* Liquidating Assets

The generated cash-flow intelligence output contained company-level classifications and financial indicators.

## Distress Logic

A separate distress condition was implemented for:

```text
CFO < 0 and CFF > 0
```

This was kept separate from the capital-allocation classification so that a distress condition does not incorrectly change the primary capital-allocation label.

## Cash-Flow Testing

The cash-flow analysis and capital-allocation logic were tested successfully.

The KPI test suite reached:

```text
69 passed
```

---

# Automated Reports

Sprint 5 also introduced automated reporting functionality.

Reports were generated for:

* Company tearsheets
* Sector analysis
* Screener results
* Peer groups
* Portfolio analysis

The project also generated Excel and CSV outputs for downstream analysis.

---

# Sprint 6 — Clustering, REST API & QA

## Objective

Sprint 6 focused on advanced company clustering, REST API development, automated testing, and final project validation.

---

# Company Clustering

A KMeans clustering model was developed to group all 92 companies into financial archetypes.

## Features Used

The clustering model uses:

* Return on Equity
* Debt to Equity
* Revenue CAGR
* FCF CAGR
* Operating Profit Margin

## Data Preparation

Missing values were handled using:

1. Broad-sector median
2. Overall median fallback

The features were standardized before clustering.

## KMeans Configuration

The clustering implementation uses:

* 5 clusters
* `random_state = 42`
* `n_init = 10`

## Financial Archetypes

The five generated archetypes are:

* Defensive Dividend Payers
* Distressed or Turnaround
* Emerging Growth
* High-Quality Compounders
* Value Cyclicals

All **92 companies** received a cluster assignment.

## Cluster Distribution

| Archetype                 | Companies |
| ------------------------- | --------: |
| Defensive Dividend Payers |        14 |
| Distressed or Turnaround  |        15 |
| Emerging Growth           |         1 |
| High-Quality Compounders  |        60 |
| Value Cyclicals           |         2 |
| **Total**                 |    **92** |

## Clustering Outputs

```text
output/cluster_labels.csv
output/cluster_profile.csv
output/outlier_report.csv
output/portfolio_stats.csv
```

Visualizations:

```text
reports/elbow_plot.png
reports/correlation_heatmap.png
```

---

# Outlier Analysis

Sector-level Z-score analysis was performed to identify unusual observations.

The analysis identified:

* **9 sector-level Z-score outliers**

These observations were included in the outlier report for further analysis.

---

# REST API

A REST API was developed using:

* FastAPI
* Uvicorn
* SQLite

API source:

```text
src/api/
```

## API Features

The API provides access to:

* Companies
* Profit & Loss
* Balance Sheet
* Cash Flow
* Financial Ratios
* Company tearsheets
* Screener
* Sectors
* Peer groups
* Valuation
* Market capitalization
* Portfolio statistics
* Documents

---

# API Endpoints

The implemented business endpoints include:

```text
GET /api/v1/companies
GET /api/v1/companies/{ticker}
GET /api/v1/companies/{ticker}/pl
GET /api/v1/companies/{ticker}/bs
GET /api/v1/companies/{ticker}/cashflow
GET /api/v1/companies/{ticker}/ratios
GET /api/v1/companies/{ticker}/tearsheet

GET /api/v1/screener

GET /api/v1/sectors
GET /api/v1/sectors/{sector}/companies

GET /api/v1/peers/{ticker}
GET /api/v1/peers/{ticker}/compare

GET /api/v1/valuation
GET /api/v1/market-cap

GET /api/v1/portfolio/stats

GET /api/v1/documents
GET /api/v1/documents/{ticker}
```

Health endpoints:

```text
GET /api/v1/health
GET /
```

---

# Swagger API Documentation

FastAPI automatically provides interactive API documentation.

After starting the server, open:

```text
http://127.0.0.1:8000/docs
```

The OpenAPI schema was also generated as:

```text
output/openapi.json
```

---

# API Validation

All implemented business endpoints were manually tested.

Validation included:

* Health check
* Company listing
* Company details
* Profit & Loss
* Balance Sheet
* Cash Flow
* Financial Ratios
* Tearsheet PDF generation
* Screener
* Sector listing
* Sector companies
* Peer groups
* Peer comparison
* Valuation
* Market capitalization
* Portfolio statistics
* Documents
* Company-specific documents

Example validation:

```text
TCS P&L       → 200 OK
TCS BS        → 200 OK
TCS Cash Flow → 200 OK
TCS Ratios    → 200 OK
TCS Tearsheet → 200 OK
Screener      → 200 OK
Valuation     → 200 OK
```

---

# Automated Testing

The project uses **Pytest** for automated validation.

Final Sprint 6 test result:

```text
147 passed
1 warning
0 failed
```

The warning originated from a third-party Starlette/AnyIO deprecation and did not cause a project test failure.

The API test suite and KPI-related tests were included in the final validation.

---

# Sprint 6 Acceptance Validation

The Sprint 6 acceptance checklist contained **20 acceptance gates**.

Final result:

```text
20 / 20 acceptance gates verified
```

The final validation covered:

* Clustering
* Cluster assignments
* Cluster profiling
* Outlier analysis
* Portfolio statistics
* REST API
* Swagger documentation
* Endpoint correctness
* API testing
* Automated test suite
* Project outputs
* Final QA

---

# Final Project Outputs

The project generates multiple analytical outputs.

## Financial Outputs

```text
output/valuation_summary.xlsx
output/valuation_flags.csv
output/cashflow_intelligence.xlsx
output/cashflow_kpis.xlsx
output/cashflow_cfo_quality.csv
output/cashflow_distress.csv
```

## NLP Outputs

```text
output/analysis_parsed.csv
output/pros_cons_generated.csv
output/cagr_cross_validation.csv
output/parse_failures.csv
```

## Clustering Outputs

```text
output/cluster_labels.csv
output/cluster_profile.csv
output/outlier_report.csv
output/portfolio_stats.csv
```

## API Outputs

```text
output/openapi.json
output/Nifty100_API_Postman_Collection.json
```

## Reports

```text
reports/tearsheets/
reports/sector/
reports/screener/
reports/peer_group/
reports/portfolio/
```

---

# Database

The main SQLite database is:

```text
data/nifty100.db
```

The database contains structured financial information for **92 Nifty 100 companies**.

The database is intentionally excluded from Git version control through `.gitignore`.

---

# Running the Project

## 1. Activate the Virtual Environment

From the project directory:

```powershell
.venv\Scripts\Activate.ps1
```

## 2. Run the Streamlit Dashboard

Use the appropriate Streamlit application entry point from the project.

Example:

```powershell
streamlit run <dashboard_file>.py
```

The dashboard will open in the browser.

---

# Running the REST API

Activate the virtual environment first:

```powershell
.venv\Scripts\Activate.ps1
```

Then run:

```powershell
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

The API will run at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/api/v1/health
```

---

# Running Tests

Activate the virtual environment and run:

```powershell
pytest -q
```

Expected final project validation:

```text
147 passed
```

---

# Git & GitHub

The project is maintained using Git and hosted on GitHub.

Repository:

```text
janvi9960/nifty100_project
```

The completed Sprint 5 and Sprint 6 implementation was committed and pushed successfully.

Final Sprint 6 commit:

```text
a671481
```

The local `main` branch is synchronized with the remote `origin/main`.

---

# Sprint Summary

| Sprint   | Main Focus                            | Status    |
| -------- | ------------------------------------- | --------- |
| Sprint 1 | Data Ingestion & ETL                  | Completed |
| Sprint 2 | Financial Statement & Ratio Analysis  | Completed |
| Sprint 3 | Screener & Peer Analysis              | Completed |
| Sprint 4 | Streamlit Dashboard & Valuation       | Completed |
| Sprint 5 | NLP, Cash-Flow Intelligence & Reports | Completed |
| Sprint 6 | Clustering, REST API & QA             | Completed |

---

# Final Project Status

The Nifty 100 Financial Intelligence Platform has progressed from raw financial data ingestion to a complete analytical platform.

The completed system provides:

* Financial data ingestion
* ETL and normalization
* SQLite financial database
* Financial statement analysis
* Financial ratio analysis
* Company screening
* Peer comparison
* Sector analysis
* Valuation analysis
* NLP-based financial insights
* Automated pros and cons
* Cash-flow intelligence
* Capital allocation classification
* Distress analysis
* KMeans company clustering
* Outlier detection
* Portfolio statistics
* Interactive Streamlit dashboard
* FastAPI REST API
* Swagger documentation
* Automated PDF reports
* Excel and CSV outputs
* Automated testing

**Final Sprint 6 QA result: 147 tests passed, 0 failures.**

**Sprint 6 acceptance result: 20/20 gates verified.**

---

## Project Status

**Sprints 1–6: Completed ✅**

**Nifty 100 Financial Intelligence Platform: Successfully implemented and validated.**
