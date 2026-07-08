import io
import os
import time
import uuid
import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import RoleChecker, get_current_user
from app.models.models import User, UploadHistory, AuditLog, Dataset, ColumnMetadata, GeneratedKPI, GeneratedInsight
from app.schemas.schemas import UploadReport
from app.services.ingestion import clean_dataframe
from app.services.metadata_engine import MetadataEngine

router = APIRouter()

@router.post("/ingest", response_model=UploadReport)
def ingest_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["CEO", "Data_Analyst"]))
):
    filename = file.filename
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only CSV and Excel files are supported."
        )
        
    try:
        contents = file.file.read()
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse uploaded file: {str(e)}"
        )
        
    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )
        
    # Process base cleaning
    start_time = time.time()
    df_cleaned, clean_report = clean_dataframe(df)
    cleaning_time = round(time.time() - start_time, 4)
    
    # Generate database identifiers
    dataset_id = uuid.uuid4()
    
    # Save cleaned data to Parquet storage
    try:
        storage_dir = os.path.join("storage", "datasets")
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, f"{dataset_id}.parquet")
        df_cleaned.to_parquet(file_path, index=False)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store cleaned dataset on server: {str(e)}"
        )
        
    try:
        # Detect Columns, Types, Stats
        columns_profile = MetadataEngine.detect_schema_and_profile(df_cleaned)
        
        # Determine Domain & Confidence
        domain_name, confidence = MetadataEngine.classify_dataset_domain(columns_profile)
        
        # Create Dataset Metadata Row
        dataset_row = Dataset(
            dataset_id=dataset_id,
            filename=filename,
            domain=domain_name,
            confidence_score=confidence,
            record_count=len(df_cleaned),
            uploaded_by=current_user.user_id
        )
        db.add(dataset_row)
        db.commit()
        
        # Save Columns Profile
        for col in columns_profile:
            col_metadata = ColumnMetadata(
                dataset_id=dataset_id,
                column_name=col["column_name"],
                data_type=col["data_type"],
                semantic_type=col["semantic_type"],
                null_percentage=col["null_percentage"],
                distinct_count=col["distinct_count"],
                min_value=col["min_value"],
                max_value=col["max_value"],
                mean_value=col["mean_value"],
                median_value=col["median_value"],
                std_dev_value=col["std_dev_value"]
            )
            db.add(col_metadata)
        db.commit()
        
        # Generate Suggested KPIs
        suggested_kpis, suggested_charts = MetadataEngine.suggest_kpis_and_charts(columns_profile)
        for k in suggested_kpis:
            # We will calculate display values dynamically during dashboard queries
            kpi_row = GeneratedKPI(
                dataset_id=dataset_id,
                kpi_name=k["name"],
                formula=k["formula"],
                display_value="Pending"
            )
            db.add(kpi_row)
            
        # Generate Suggested Insights
        insights = []
        insights.append(f"Successfully identified dataset domain as **{domain_name}** with **{confidence}%** confidence.")
        insights.append(f"Ingested **{len(df_cleaned):,}** records across **{len(columns_profile)}** distinct column fields.")
        
        # Detect numeric distributions or null warnings
        null_cols = [c["column_name"] for c in columns_profile if c["null_percentage"] > 10.0]
        if null_cols:
            insights.append(f"**WARNING**: Columns ({', '.join(null_cols[:2])}) contain high missing value percentages. Mode/median substitution applied.")
            
        for text_insight in insights:
            ins_row = GeneratedInsight(
                dataset_id=dataset_id,
                text=text_insight,
                severity="info"
            )
            db.add(ins_row)
        db.commit()
        
        # Create Upload History log
        upload_log = UploadHistory(
            upload_id=dataset_id,
            filename=filename,
            uploaded_by=current_user.user_id,
            status="Success",
            records_processed=len(df_cleaned)
        )
        db.add(upload_log)
        
        # Create Audit Log
        audit = AuditLog(
            user_id=current_user.user_id,
            action="INGEST_SCHEMA_AWARE",
            table_name="datasets",
            record_id=str(dataset_id),
            details=f"Uploaded and parsed business dataset {filename}. Domain classified as {domain_name}."
        )
        db.add(audit)
        db.commit()
        
        # Format uploader response
        return {
            "upload_id": dataset_id,
            "filename": filename,
            "status": "Success",
            "total_records": clean_report["total_records"],
            "processed_records": len(df_cleaned),
            "null_report": clean_report["null_report"],
            "duplicates_removed": clean_report["duplicates_removed"],
            "outliers_detected": clean_report["outliers_detected"],
            "cleaning_time_seconds": cleaning_time,
            "domain": domain_name,
            "confidence_score": confidence,
            "columns": columns_profile
        }
        
    except Exception as e:
        db.rollback()
        # Clean up parquet file if db fails
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
                
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record dataset metadata: {str(e)}"
        )
