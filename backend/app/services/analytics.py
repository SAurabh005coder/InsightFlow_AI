import os
import uuid
import duckdb
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.models import Dataset, ColumnMetadata, GeneratedKPI, GeneratedInsight, User

class AnalyticsService:
    @staticmethod
    def get_datasets_list(db: Session, user_id: str) -> List[Dict[str, Any]]:
        import uuid
        try:
            user_uuid = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return []
            
        rows = db.query(Dataset).filter(Dataset.uploaded_by == user_uuid).order_by(Dataset.created_at.desc()).all()
        return [
            {
                "dataset_id": str(r.dataset_id),
                "filename": r.filename,
                "domain": r.domain,
                "confidence_score": float(r.confidence_score),
                "record_count": int(r.record_count),
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(r.created_at, "strftime") else str(r.created_at)
            }
            for r in rows
        ]

    @staticmethod
    def get_dashboard_summary(db: Session, dataset_id: str = None, user_id: str = None) -> Dict[str, Any]:
        import uuid
        
        user_uuid = None
        if user_id:
            try:
                user_uuid = uuid.UUID(str(user_id))
            except (ValueError, TypeError):
                pass

        # 1. Resolve dataset_id
        if not dataset_id:
            # Find the most recently uploaded dataset by this user
            if user_uuid:
                recent_ds = db.query(Dataset).filter(Dataset.uploaded_by == user_uuid).order_by(Dataset.created_at.desc()).first()
            else:
                recent_ds = db.query(Dataset).order_by(Dataset.created_at.desc()).first()
                
            if not recent_ds:
                # Return empty dashboard summary state
                return {
                    "dataset_id": "",
                    "filename": "None",
                    "domain": "Generic Business Dataset",
                    "confidence_score": 0.0,
                    "record_count": 0,
                    "kpis": [],
                    "charts": [],
                    "insights": ["No business datasets uploaded yet. Go to Upload Dataset to import a file."]
                }
            dataset_id = str(recent_ds.dataset_id)
            
        try:
            dataset_uuid = uuid.UUID(str(dataset_id))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid dataset ID format: {dataset_id}")
            
        ds = db.query(Dataset).filter(Dataset.dataset_id == dataset_uuid).first()
        if not ds:
            raise ValueError(f"Dataset with ID {dataset_id} not found.")
            
        if user_uuid and ds.uploaded_by != user_uuid:
            # If the dataset doesn't belong to this user, try to get their most recent one
            recent_ds = db.query(Dataset).filter(Dataset.uploaded_by == user_uuid).order_by(Dataset.created_at.desc()).first()
            if not recent_ds:
                return {
                    "dataset_id": "",
                    "filename": "None",
                    "domain": "Generic Business Dataset",
                    "confidence_score": 0.0,
                    "record_count": 0,
                    "kpis": [],
                    "charts": [],
                    "insights": ["No business datasets uploaded yet. Go to Upload Dataset to import a file."]
                }
            ds = recent_ds
            dataset_uuid = ds.dataset_id
            
        file_path = os.path.join("storage", "datasets", f"{dataset_uuid}.parquet")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Parquet file for dataset {dataset_uuid} is missing.")
            
        # 2. Query KPIs dynamically using DuckDB
        kpi_list = []
        kpis_db = db.query(GeneratedKPI).filter(GeneratedKPI.dataset_id == dataset_uuid).all()
        
        for k in kpis_db:
            formula = k.formula
            try:
                # Run dynamic formula on the parquet file in DuckDB
                res = duckdb.query(f"SELECT {formula} AS val FROM '{file_path}'").to_df()
                raw_val = res.iloc[0]["val"]
                
                # Formatting
                if pd.isna(raw_val):
                    display = "0"
                elif isinstance(raw_val, (int, np.integer)):
                    display = f"{int(raw_val):,}"
                elif isinstance(raw_val, (float, np.floating)):
                    if "SUM" in formula or "AVG" in formula:
                        display = f"${float(raw_val):,.2f}" if "sales" in formula.lower() or "price" in formula.lower() or "revenue" in formula.lower() or "monetary" in formula.lower() else f"{float(raw_val):,.2f}"
                    else:
                        display = f"{float(raw_val):,.2f}"
                else:
                    display = str(raw_val)
            except Exception as e:
                display = "Error"
                
            kpi_list.append({
                "name": k.kpi_name,
                "value": display,
                "formula": formula
            })
            
        # 3. Query Visualizations dynamically using DuckDB
        charts_list = []
        columns = db.query(ColumnMetadata).filter(ColumnMetadata.dataset_id == dataset_uuid).all()
        monetary_cols = [c.column_name for c in columns if c.semantic_type == "Monetary"]
        qty_cols = [c.column_name for c in columns if c.semantic_type == "Quantity"]
        number_cols = [c.column_name for c in columns if c.semantic_type == "Number"]
        
        date_cols = [c.column_name for c in columns if c.semantic_type == "Date"]
        geo_cols = [c.column_name for c in columns if c.semantic_type == "Geographic"]
        text_cols = [c.column_name for c in columns if c.semantic_type == "Text"]
        
        measure_col = monetary_cols[0] if monetary_cols else (qty_cols[0] if qty_cols else (number_cols[0] if number_cols else None))
        
        # 3.1 Line Chart: Time series grouping
        if date_cols and measure_col:
            try:
                # Group by Date
                res_line = duckdb.query(f"""
                    SELECT CAST({date_cols[0]} AS DATE) AS date_axis, SUM({measure_col}) AS val
                    FROM '{file_path}'
                    GROUP BY date_axis
                    ORDER BY date_axis ASC
                    LIMIT 100
                """).to_df()
                res_line["date_axis"] = res_line["date_axis"].astype(str)
                charts_list.append({
                    "type": "Line Chart",
                    "title": f"{measure_col.replace('_', ' ').title()} Over Time",
                    "x_axis": date_cols[0],
                    "y_axis": measure_col,
                    "data": res_line.rename(columns={"date_axis": "date", "val": "value"}).to_dict(orient="records")
                })
            except Exception:
                pass
                
        # 3.2 Category Split: Pie Chart
        cat_col = text_cols[0] if text_cols else (geo_cols[0] if geo_cols else None)
        if cat_col and measure_col:
            try:
                res_pie = duckdb.query(f"""
                    SELECT {cat_col} AS cat_axis, SUM({measure_col}) AS val
                    FROM '{file_path}'
                    GROUP BY cat_axis
                    ORDER BY val DESC
                    LIMIT 8
                """).to_df()
                charts_list.append({
                    "type": "Pie Chart",
                    "title": f"{measure_col.replace('_', ' ').title()} Split by {cat_col.replace('_', ' ').title()}",
                    "x_axis": cat_col,
                    "y_axis": measure_col,
                    "data": res_pie.rename(columns={"cat_axis": "name", "val": "value"}).to_dict(orient="records")
                })
            except Exception:
                pass
                
        # 3.3 Location Rankings: Bar Chart
        bar_col = geo_cols[0] if geo_cols else (text_cols[1] if len(text_cols) > 1 else None)
        if bar_col and measure_col:
            try:
                res_bar = duckdb.query(f"""
                    SELECT {bar_col} AS rank_axis, SUM({measure_col}) AS val
                    FROM '{file_path}'
                    GROUP BY rank_axis
                    ORDER BY val DESC
                    LIMIT 10
                """).to_df()
                charts_list.append({
                    "type": "Bar Chart",
                    "title": f"Top Rankings by {bar_col.replace('_', ' ').title()}",
                    "x_axis": bar_col,
                    "y_axis": measure_col,
                    "data": res_bar.rename(columns={"rank_axis": "name", "val": "value"}).to_dict(orient="records")
                })
            except Exception:
                pass

        # 4. Compile Insights dynamically
        insight_list = []
        insights_db = db.query(GeneratedInsight).filter(GeneratedInsight.dataset_id == dataset_uuid).all()
        for ins in insights_db:
            insight_list.append(ins.text)
            
        # Add dynamic skewness checks for numeric columns
        for col in columns:
            if col.data_type in ["Integer", "Float"] and col.mean_value is not None:
                try:
                    skew_df = duckdb.query(f"SELECT skewness({col.column_name}) AS skew FROM '{file_path}'").to_df()
                    skew = float(skew_df.iloc[0]["skew"])
                    if skew > 1.0:
                        insight_list.append(f"The **{col.column_name}** data distribution exhibits positive skewness (**{skew:.2f}**), indicating high concentration of values on the lower end.")
                    elif skew < -1.0:
                        insight_list.append(f"The **{col.column_name}** data distribution exhibits negative skewness (**{skew:.2f}**), indicating high concentration on the upper end.")
                except Exception:
                    pass
                    
        return {
            "dataset_id": str(ds.dataset_id),
            "filename": ds.filename,
            "domain": ds.domain,
            "confidence_score": float(ds.confidence_score),
            "record_count": ds.record_count,
            "kpis": kpi_list,
            "charts": charts_list,
            "insights": insight_list
        }
