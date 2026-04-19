# Nifty 100 Financial Intelligence System

ML-powered financial analytics platform for India's top 100 listed companies.

## What This Project Does
- Analyzes 12 years of financial data for 100 Nifty companies
- Generates ML-based health scores (Profitability, Leverage, Cash Flow, Growth)
- 7 interactive Power BI dashboards
- REST API with 9 endpoints
- Public-facing website with company dashboards

## Tech Stack
- **Python 3.11** — ETL, ML scoring
- **PostgreSQL** — Data warehouse
- **Power BI** — 7 analytics dashboards
- **Django + DRF** — Web app + REST API
- **Chart.js** — Interactive charts
- **Jupyter** — EDA notebooks

## Project Structure
nifty100/
├── etl/                  # ETL pipeline scripts
│   ├── 01_extract_from_excel.py
│   ├── 02_clean_and_transform.py
│   ├── 03_load_to_warehouse.py
│   └── 04_ml_health_scores.py
├── data/                 # Raw, clean data + EDA charts
├── Nifty100_EDA.ipynb   # Exploratory Data Analysis
└── nifty100_web/        # Django web application
├── api/             # REST API
└── templates/       # Frontend pages

## API Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/companies/` | All companies |
| `GET /api/companies/{symbol}/` | Company details |
| `GET /api/companies/{symbol}/profit-loss/` | P&L data |
| `GET /api/companies/{symbol}/balance-sheet/` | Balance sheet |
| `GET /api/companies/{symbol}/cash-flow/` | Cash flow |
| `GET /api/companies/{symbol}/ml-score/` | Health score |
| `GET /api/sectors/` | All sectors |
| `GET /api/top-companies/` | Top by health score |

## How to Run
```bash
# Install dependencies
pip install pandas openpyxl psycopg2-binary sqlalchemy djangorestframework scikit-learn

# Run ETL
py -3.11 etl/01_extract_from_excel.py
py -3.11 etl/02_clean_and_transform.py
py -3.11 etl/03_load_to_warehouse.py
py -3.11 etl/04_ml_health_scores.py

# Run Django server
cd nifty100_web
py -3.11 manage.py runserver
```

## Dashboards
1. Company Overview
2. Sector Analysis
3. Financial Health Scorecard
4. Profitability Deep Dive
5. Balance Sheet Analysis
6. Cash Flow Analysis
7. Growth Trends

## Author
Ronit Gulia — Internship Project