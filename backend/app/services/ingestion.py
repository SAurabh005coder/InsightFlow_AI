import io
import time
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any

def infer_column_type(series: pd.Series) -> str:
    """
    Dynamically infers the datatype of a column series.
    Returns: 'Integer', 'Float', 'DateTime', 'Boolean', or 'Text'.
    """
    non_null = series.dropna()
    if len(non_null) == 0:
        return "Text"
        
    dtype_str = str(non_null.dtype)
    if "int" in dtype_str:
        return "Integer"
    if "float" in dtype_str:
        return "Float"
    if "datetime" in dtype_str or "date" in dtype_str:
        return "DateTime"
    if "bool" in dtype_str:
        return "Boolean"
        
    # Check if values are mostly numeric (stripping common currency signs and commas)
    try:
        cleaned_str = non_null.astype(str).str.replace(r'[\$,]', '', regex=True)
        temp_numeric = pd.to_numeric(cleaned_str, errors='coerce')
        non_null_numeric = temp_numeric.dropna()
        if len(non_null_numeric) > len(non_null) * 0.8:
            # If all are integers, classify as Integer
            if (non_null_numeric % 1 == 0).all():
                return "Integer"
            return "Float"
    except Exception:
        pass
        
    # Check if values can be parsed as dates
    try:
        # Sample values for performance on large tables
        sample_size = min(len(non_null), 100)
        sample = non_null.sample(sample_size, random_state=42)
        parsed = pd.to_datetime(sample, errors='coerce', format='mixed')
        if parsed.notna().sum() > sample_size * 0.8:
            return "DateTime"
    except Exception:
        pass
        
    # Check if values can be interpreted as booleans
    try:
        unique_vals = set(non_null.astype(str).str.strip().str.lower().unique())
        if unique_vals.issubset({'true', 'false', '1', '0', 'yes', 'no', 'y', 'n', 't', 'f', 'active', 'inactive'}):
            return "Boolean"
    except Exception:
        pass
        
    return "Text"

def clean_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans the input DataFrame dynamically based on inferred column datatypes.
    Handles null values, formats currencies, standardizes dates and booleans,
    and detects statistical outliers using the IQR method.
    """
    report = {
        "total_records": len(df),
        "null_report": {},
        "duplicates_removed": 0,
        "outliers_detected": 0,
        "cleaning_time_seconds": 0.0
    }
    
    if df.empty:
        return df, report
        
    start_time = time.time()
    
    # 1. Prune exact duplicate rows
    initial_len = len(df)
    df = df.drop_duplicates()
    report["duplicates_removed"] = initial_len - len(df)
    
    # Record original null percentage before cleaning
    for col in df.columns:
        null_pct = (df[col].isna().sum() / len(df)) * 100
        report["null_report"][col] = round(null_pct, 2)
        
    # 2. Iterate and clean dynamically based on inferred schema types
    for col in df.columns:
        inferred_type = infer_column_type(df[col])
        
        if inferred_type in ["Integer", "Float"]:
            # Standardize numeric inputs
            if not pd.api.types.is_numeric_dtype(df[col]):
                cleaned_series = df[col].astype(str).str.replace(r'[\$,]', '', regex=True)
            else:
                cleaned_series = df[col]
                
            numeric_col = pd.to_numeric(cleaned_series, errors='coerce')
            
            # Median Imputation
            median_val = numeric_col.median()
            if pd.isna(median_val):
                median_val = 0.0
            df[col] = numeric_col.fillna(median_val)
            
            # Type casting to clean float
            df[col] = df[col].astype(float)
            if inferred_type == "Float":
                df[col] = df[col].round(4)
                
            # Outlier Detection (Interquartile Range)
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = df[(df[col] < lower) | (df[col] > upper)]
            report["outliers_detected"] += len(outliers)
            
        elif inferred_type == "DateTime":
            # Date conversions
            parsed_dates = pd.to_datetime(df[col], errors='coerce', format='mixed')
            # Dynamic imputation: forward fill, backward fill, or current timestamp fallback
            df[col] = parsed_dates.ffill().bfill().fillna(pd.Timestamp.now())
            
        elif inferred_type == "Boolean":
            # Boolean conversions
            def to_bool(val):
                if pd.isna(val):
                    return None
                val_str = str(val).strip().lower()
                if val_str in ['true', '1', '1.0', 'yes', 'y', 't', 'active']:
                    return True
                if val_str in ['false', '0', '0.0', 'no', 'n', 'f', 'inactive']:
                    return False
                return None
                
            bool_series = df[col].apply(to_bool)
            mode_val = bool_series.mode()
            fallback = True if len(mode_val) == 0 else bool(mode_val[0])
            df[col] = bool_series.fillna(fallback).astype(bool)
            
        else: # Text / Categorical
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": np.nan, "None": np.nan, "": np.nan})
            
            # Mode Imputation
            non_null_text = df[col].dropna()
            if len(non_null_text) > 0 and non_null_text.nunique() > 0:
                mode_val = non_null_text.mode()[0]
                df[col] = df[col].fillna(mode_val)
            else:
                df[col] = df[col].fillna("Unknown")
                
    # 3. Derived Columns Heuristics
    if "net_amount" not in df.columns and "quantity" in df.columns and "unit_price" in df.columns:
        df["net_amount"] = df["quantity"] * df["unit_price"]
        
    report["cleaning_time_seconds"] = round(time.time() - start_time, 4)
    return df, report
