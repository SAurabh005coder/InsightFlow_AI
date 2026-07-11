from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import RoleChecker, get_current_user
from app.schemas.schemas import DynamicDashboardResponse, ForecastResponse, DatasetResponse
from app.services.analytics import AnalyticsService
from app.services.ml import MLService
from typing import Dict, Any, List, Optional

router = APIRouter()

@router.get("/datasets", response_model=List[Dict[str, Any]])
def list_datasets(
    db: Session = Depends(get_db),
    current_user = Depends(RoleChecker(["CEO", "Store_Manager", "Sales_Manager", "Data_Analyst"]))
):
    try:
        datasets = AnalyticsService.get_datasets_list(db, str(current_user.user_id))
        return datasets
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query datasets ledger: {str(e)}"
        )

@router.get("/dashboard", response_model=DynamicDashboardResponse)
def get_dashboard(
    dataset_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(RoleChecker(["CEO", "Store_Manager", "Sales_Manager", "Data_Analyst"]))
):
    try:
        data = AnalyticsService.get_dashboard_summary(db, dataset_id, user_id=str(current_user.user_id))
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compile metadata dashboard: {str(e)}"
        )

@router.get("/forecast", response_model=ForecastResponse)
def get_forecast(
    dataset_id: Optional[str] = Query(None),
    days: int = 90,
    db: Session = Depends(get_db),
    current_user = Depends(RoleChecker(["CEO", "Data_Analyst"]))
):
    try:
        from app.api.deps import get_verified_dataset_id
        dataset_id = get_verified_dataset_id(db, dataset_id, current_user.user_id)
        forecast_data = MLService.forecast_sales(db, dataset_id, days_ahead=days)
        return forecast_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ML Forecasting algorithm failed: {str(e)}"
        )

@router.get("/segmentation")
def get_segmentation(
    dataset_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(RoleChecker(["CEO", "Data_Analyst"]))
):
    try:
        from app.api.deps import get_verified_dataset_id
        dataset_id = get_verified_dataset_id(db, dataset_id, current_user.user_id)
        segments_data = MLService.segment_customers(db, dataset_id)
        return segments_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Clustering segmentation failed: {str(e)}"
        )

@router.get("/records")
def get_dataset_records(
    dataset_id: Optional[str] = Query(None),
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    import os
    import duckdb
    import numpy as np
    from app.models.models import Dataset, ColumnMetadata
    from app.api.deps import get_verified_dataset_id
    
    import uuid
    try:
        dataset_id = get_verified_dataset_id(db, dataset_id, current_user.user_id)
    except HTTPException:
        return {"columns": [], "records": [], "total": 0}
        
    try:
        dataset_uuid = uuid.UUID(str(dataset_id))
    except (ValueError, TypeError):
        return {"columns": [], "records": [], "total": 0}
        
    file_path = os.path.join("storage", "datasets", f"{dataset_uuid}.parquet")
    if not os.path.exists(file_path):
        return {"columns": [], "records": [], "total": 0}
        
    cols = db.query(ColumnMetadata).filter(ColumnMetadata.dataset_id == dataset_uuid).all()
    col_names = [c.column_name for c in cols]
    
    if not col_names:
        return {"columns": [], "records": [], "total": 0}
        
    query = f"SELECT * FROM '{file_path}'"
    if search:
        search_escaped = search.replace("'", "''")
        clauses = [f"CAST({c} AS VARCHAR) ILIKE '%{search_escaped}%'" for c in col_names]
        query += " WHERE " + " OR ".join(clauses)
        
    try:
        count_df = duckdb.query(f"SELECT COUNT(*) as cnt FROM ({query})").to_df()
        total_count = int(count_df.iloc[0]["cnt"])
    except Exception:
        total_count = 0
        
    query += f" LIMIT {limit} OFFSET {offset}"
    
    try:
        df = duckdb.query(query).to_df()
        df = df.replace({np.nan: None})
        records = df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query records: {str(e)}")
        
    return {
        "columns": col_names,
        "records": records,
        "total": total_count
    }
