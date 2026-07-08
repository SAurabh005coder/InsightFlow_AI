# RetailIQ - AI-Powered Retail Business Analytics Platform

RetailIQ is an enterprise-grade, B2B Business Intelligence (BI) and predictive analytics application designed to ingest raw Point-of-Sale (POS) transactions, clean it, execute sub-second multi-dimensional analytical queries, and output predictive forecasting and machine learning metrics. 

Designed specifically as an **MCA Semester 3 Minor Project** and constructed with senior software engineering standards.

---

## 🛠️ Technology Stack

* **Frontend**: React (v18), TypeScript, Vite, Tailwind CSS (v4), Plotly, React Router, TanStack React Query, Axios, Lucide Icons.
* **Backend**: Python (3.12+), FastAPI, SQLAlchemy ORM, Pydantic, Bcrypt, PyTest.
* **Database Layer**: PostgreSQL 16+ (Transactional Ledger / OLTP) & DuckDB (Vectorized Analytical Engine / OLAP).
* **Analytics & ML Core**: Pandas, NumPy, Scikit-learn (K-Means Clustering), Statsmodels (Holt-Winters / Exponential Smoothing).
* **Document Exporters**: ReportLab (Styled PDFs) and OpenPyXL (Multi-sheet Excel).

---

## 📐 System Architecture & Data Flow

```
                                  +---------------------+
                                  |    Uploaded File    |
                                  |     (CSV/Excel)     |
                                  +----------+----------+
                                             |
                                             v
                                  +----------+----------+
                                  |   FastAPI Ingest    |
                                  |    (Schema Validation)
                                  +----------+----------+
                                             |
                                             v
                                  +----------+----------+
                                  |   ETL Cleaning      |
                                  |  (Impute, Outliers) |
                                  +----------+----------+
                                             |
                                             v
                             +---------------+---------------+
                             |                               |
                             v                               v
                 +-----------+-----------+       +-----------+-----------+
                 |   PostgreSQL Database |       |   Pandas DataFrames   |
                 |      (OLTP Store)     |       |                       |
                 +-----------------------+       +-----------+-----------+
                                                             |
                                                             v
                                                 +-----------+-----------+
                                                 |     DuckDB OLAP       |
                                                 |   (Vectorized Query)  |
                                                 +-----------+-----------+
                                                             |
                                                             v
                                                 +-----------+-----------+
                                                 |   Analytics Summary   |
                                                 |  & Forecast Outputs   |
                                                 +-----------------------+
```

---

## 💾 Relational Database Schema (3NF)

RetailIQ's database is fully normalized to Third Normal Form (3NF) standard containing 15 tables:
1. **roles**: User roles (CEO, Store_Manager, Sales_Manager, Data_Analyst).
2. **users**: Platform credentials and activation flags.
3. **stores**: Regional retail branch locations.
4. **categories**: Product groupings with parent hierarchies.
5. **products**: Catalog items, unit cost/retail pricing constraints.
6. **customers**: Customer registry and K-Means segmentation labels.
7. **orders**: Transaction header (order date, store, total amount).
8. **order_items**: Transaction details (SKUs, quantity, net amount).
9. **inventory**: Stock trackers with reorder points and safety limits.
10. **suppliers**: Product supplier contacts.
11. **employees**: Branch staff rosters and roles.
12. **payments**: Checkout payment methods and statuses.
13. **returns**: Customer product refunds and logs.
14. **upload_history**: CSV uploader metadata and cleaning logs.
15. **audit_logs**: Internal user action logs.

---

## 🚀 Setup & Installation Guide

### Prerequisites
* **Node.js** v20+ & **npm**
* **Python** v3.11 / v3.12 / v3.14+
* **PostgreSQL** running locally on port `5432` (Optional. Application automatically falls back to an SQLite database file `retailiq.db` if PostgreSQL is unreachable).

### 1. Backend Service Configuration
1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Set up the virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install package requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Seed mock retail transactions (generates a `retail_sample.csv` in the root folder):
   ```bash
   python generate_sample_data.py
   ```
5. Run the dev server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### 2. Frontend Application Configuration
1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Launch the hot-reloading dev environment:
   ```bash
   npm run dev
   ```
4. Access the web interface at `http://localhost:5173`.

---

## 🧪 Running Automated Tests

A comprehensive PyTest suite covers authentication flows, token generation, and the ETL cleaning heuristics.
To run the test suite:
1. Navigate to the backend directory.
2. Run pytest with PYTHONPATH configuration:
   ```bash
   $env:PYTHONPATH="."; .venv\Scripts\pytest
   ```

---

## 📊 Sample Ingestion Walkthrough

1. Register an account as a **CEO** or **Data Analyst** in the web interface.
2. Log in using your registered credentials.
3. Click the **Upload Dataset** tab in the sidebar.
4. Drag and drop the `retail_sample.csv` file generated in your root directory.
5. Click **Execute Data Clean**. The ETL system will output duplicate removal logs, median/mode imputations, and outliers counts.
6. Return to the **Dashboard** to see the interactive charts, growth timelines, and AI briefings populated.
7. Click the **Reports** tab to download a styled PDF brief or multi-sheet Excel log.
