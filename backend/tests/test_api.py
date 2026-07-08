import os
import io
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.services.ingestion import clean_dataframe
from app.models.models import Role, Dataset

# Set up test database (SQLite file for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.sqlite"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    
    # Seed default roles
    db = TestingSessionLocal()
    try:
        for r_name in ["CEO", "Store_Manager", "Sales_Manager", "Data_Analyst"]:
            db.add(Role(role_name=r_name, description=r_name))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
        
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_db.sqlite"):
        try:
            os.remove("./test_db.sqlite")
        except Exception:
            pass

def test_auth_and_user_flows():
    # 1. Register a new user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "analyst@insightflowai.com",
            "password": "securepassword123",
            "first_name": "Saurabh",
            "last_name": "Sahu",
            "role_name": "Data_Analyst"
        }
    )
    assert register_response.status_code == 200
    data = register_response.json()
    assert data["email"] == "analyst@insightflowai.com"
    assert data["first_name"] == "Saurabh"

    # 2. Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "analyst@insightflowai.com",
            "password": "securepassword123"
        }
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["role"] == "Data_Analyst"

def test_data_cleaning_logic():
    # Build a DataFrame with nulls and outliers
    df = pd.DataFrame([
        {"quantity": 5, "unit_price": "$10.00", "cost_price": 5.0, "insightflow_price": 10.0, "category_name": "Electronics"},
        {"quantity": 10, "unit_price": "10.00", "cost_price": 5.0, "insightflow_price": 10.0, "category_name": np.nan},
        {"quantity": np.nan, "unit_price": "10.00", "cost_price": 5.0, "insightflow_price": 10.0, "category_name": "Electronics"},
        {"quantity": 500, "unit_price": "10.00", "cost_price": 5.0, "insightflow_price": 10.0, "category_name": "Electronics"},
    ])
    
    cleaned_df, report = clean_dataframe(df)
    
    # Assertions
    assert report["total_records"] == 4
    assert cleaned_df["quantity"].iloc[2] == 10
    assert cleaned_df["category_name"].iloc[1] == "Electronics"
    assert report["outliers_detected"] > 0

def test_dynamic_data_cleaning_logic():
    # Ingest a non-retail (HR) dataset to test dynamic, domain-agnostic cleaning
    df = pd.DataFrame([
        {"employee_name": "John Doe", "monthly_salary": "$5,000.00", "is_active": "Active", "hire_date": "2024-01-10"},
        {"employee_name": "Jane Smith", "monthly_salary": "$6,000.00", "is_active": "Inactive", "hire_date": "2024-02-15"},
        {"employee_name": np.nan, "monthly_salary": np.nan, "is_active": np.nan, "hire_date": np.nan},
        {"employee_name": "John Doe", "monthly_salary": "$5,000.00", "is_active": "Active", "hire_date": "2024-01-10"},  # Duplicate row
    ])
    
    cleaned_df, report = clean_dataframe(df)
    
    # Assertions for duplicates
    assert report["total_records"] == 4
    assert len(cleaned_df) == 3  # One duplicate row removed
    
    # Check that monthly_salary was parsed as Float and missing imputed with median (5500.0)
    assert cleaned_df["monthly_salary"].iloc[0] == 5000.0
    assert cleaned_df["monthly_salary"].iloc[1] == 6000.0
    assert cleaned_df["monthly_salary"].iloc[2] == 5500.0
    
    # Check that is_active was parsed as Boolean and missing imputed with mode fallback
    assert cleaned_df["is_active"].iloc[0] == True
    assert cleaned_df["is_active"].iloc[1] == False
    assert isinstance(cleaned_df["is_active"].iloc[2], (bool, np.bool_))
    
    # Check that employee_name was parsed as Text and missing imputed with mode (Jane Smith)
    assert cleaned_df["employee_name"].iloc[0] == "John Doe"
    assert cleaned_df["employee_name"].iloc[2] == "Jane Smith"

def test_metadata_engine():
    from app.services.metadata_engine import MetadataEngine
    df = pd.DataFrame([
        {"salary": 50000, "employee_id": "EMP01", "attrition": "No", "hire_date": "2024-01-10"},
        {"salary": 60000, "employee_id": "EMP02", "attrition": "Yes", "hire_date": "2024-02-15"},
        {"salary": 55000, "employee_id": "EMP03", "attrition": "No", "hire_date": "2024-03-20"},
    ])
    
    profiles = MetadataEngine.detect_schema_and_profile(df)
    assert len(profiles) == 4
    
    salary_col = next(c for c in profiles if c["column_name"] == "salary")
    assert salary_col["semantic_type"] == "Monetary"
    
    domain, confidence = MetadataEngine.classify_dataset_domain(profiles)
    assert domain == "HR"
    assert confidence >= 40.0

def test_full_system_e2e():
    # 1. Register User (CEO)
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "ceo@intelligentanalytics.com",
            "password": "supersecureceo",
            "first_name": "Executive",
            "last_name": "Officer",
            "role_name": "CEO"
        }
    )
    assert reg_res.status_code == 200
    
    # 2. Login
    login_res = client.post(
        "/api/v1/auth/login",
        data={
            "username": "ceo@intelligentanalytics.com",
            "password": "supersecureceo"
        }
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Ingest Dataset
    df_mock = pd.DataFrame([
        {"order_number": "ORD-101", "order_date": "2026-06-01", "store_code": "ST01", "store_name": "Main Outlet", "region": "North", "city": "Chicago", "state": "IL", "customer_code": "CUST-01", "customer_first_name": "Saurabh", "customer_last_name": "Sahu", "sku": "SKU-01", "product_name": "Quantum Headset", "category_name": "Electronics", "quantity": 2, "unit_price": 50.00, "cost_price": 30.00, "insightflow_price": 50.00, "payment_method": "Credit Card", "status": "Success", "is_returned": 0, "refund_amount": 0.0},
        {"order_number": "ORD-102", "order_date": "2026-06-02", "store_code": "ST01", "store_name": "Main Outlet", "region": "North", "city": "Chicago", "state": "IL", "customer_code": "CUST-02", "customer_first_name": "Alice", "customer_last_name": "Smith", "sku": "SKU-02", "product_name": "Aero Fan", "category_name": "Appliances", "quantity": 1, "unit_price": 100.00, "cost_price": 60.00, "insightflow_price": 100.00, "payment_method": "PayPal", "status": "Success", "is_returned": 0, "refund_amount": 0.0}
    ])
    csv_file = io.BytesIO()
    df_mock.to_csv(csv_file, index=False)
    csv_file.seek(0)
    
    ingest_res = client.post(
        "/api/v1/datasets/ingest",
        files={"file": ("mock_dataset.csv", csv_file, "text/csv")},
        headers=headers
    )
    assert ingest_res.status_code == 200, f"Ingest failed: {ingest_res.text}"
    report = ingest_res.json()
    assert report["status"] == "Success"
    assert report["domain"] == "InsightFlow"
    assert report["confidence_score"] > 40.0
    
    dataset_id = report["upload_id"]
    
    # 4. Fetch Datasets List
    list_res = client.get("/api/v1/analytics/datasets", headers=headers)
    assert list_res.status_code == 200, f"List failed: {list_res.text}"
    datasets = list_res.json()
    assert len(datasets) > 0
    
    # 5. Fetch Dynamic Dashboard summary
    dash_res = client.get(f"/api/v1/analytics/dashboard?dataset_id={dataset_id}", headers=headers)
    assert dash_res.status_code == 200, f"Dashboard failed: {dash_res.text}"
    dash = dash_res.json()
    assert dash["dataset_id"] == dataset_id
    assert len(dash["kpis"]) > 0
    assert len(dash["charts"]) > 0
    assert len(dash["insights"]) > 0
    
    # 6. Fetch Raw Records explorer
    rec_res = client.get(f"/api/v1/analytics/records?dataset_id={dataset_id}&limit=5", headers=headers)
    assert rec_res.status_code == 200
    recs = rec_res.json()
    assert len(recs["columns"]) > 0
    assert len(recs["records"]) > 0
    
    # 7. Fetch Dynamic Forecast
    fc_res = client.get(f"/api/v1/analytics/forecast?dataset_id={dataset_id}&days=30", headers=headers)
    assert fc_res.status_code == 200
    fc = fc_res.json()
    assert len(fc["forecast"]) > 0
    
    # 8. Fetch Segmentation
    seg_res = client.get(f"/api/v1/analytics/segmentation?dataset_id={dataset_id}", headers=headers)
    assert seg_res.status_code == 200
    seg = seg_res.json()
    assert "summary" in seg
    
    # 9. Download Excel report
    xls_res = client.get(f"/api/v1/reports/export/excel?dataset_id={dataset_id}", headers=headers)
    assert xls_res.status_code == 200
    
    # 10. Download PDF report
    pdf_res = client.get(f"/api/v1/reports/export/pdf?dataset_id={dataset_id}", headers=headers)
    assert pdf_res.status_code == 200

    # Cleanup local parquet file created in test
    storage_parquet = os.path.join("storage", "datasets", f"{dataset_id}.parquet")
    if os.path.exists(storage_parquet):
        try:
            os.remove(storage_parquet)
        except Exception:
            pass
