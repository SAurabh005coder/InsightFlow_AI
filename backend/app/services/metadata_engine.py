import re
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.models.models import Dataset, ColumnMetadata, GeneratedKPI, GeneratedInsight

# Regex mapping for Semantic Classification
SEMANTIC_RULES = {
    "Monetary": r"(revenue|sales|income|amount|price|cost|spend|salary|payment|profit|tax|billing|charge|fee)",
    "Date": r"(date|time|timestamp|year|month|day|hour|invoice|created|updated|registration|hire|admission|return_date)",
    "Customer_ID": r"(customer|cust|client|user|patient|employee|visitor|member)_?id",
    "Product_ID": r"(product|item|sku|inventory|asset|stock|equipment)_?id",
    "Geographic": r"(city|state|country|region|lat|long|latitude|longitude|address|zip|postcode|continent)",
    "Quantity": r"(quantity|qty|units|volume|count|ordered|sold|items_count)",
    "Percentage": r"(percentage|pct|margin|discount|rate|ratio|percent|score|fraction)",
    "Email": r"(email|mail|contact_email)",
    "Phone": r"(phone|mobile|telephone|fax)",
    "Boolean": r"(active|is_|has_|flag|status|enabled|deleted)"
}

class MetadataEngine:
    @staticmethod
    def detect_schema_and_profile(df: pd.DataFrame) -> List[Dict[str, Any]]:
        profiles = []
        total_rows = len(df)
        
        for col in df.columns:
            series = df[col]
            null_pct = float((series.isna().sum() / total_rows) * 100)
            distinct_cnt = int(series.nunique())
            cardinality = float(distinct_cnt / total_rows) if total_rows > 0 else 0.0
            
            # Infer data type
            dtype_str = str(series.dtype)
            if "int" in dtype_str:
                inferred_type = "Integer"
            elif "float" in dtype_str:
                inferred_type = "Float"
            elif "datetime" in dtype_str or "date" in dtype_str:
                inferred_type = "DateTime"
            elif "bool" in dtype_str:
                inferred_type = "Boolean"
            else:
                # Test if string can be parsed as numeric or date
                temp_numeric = pd.to_numeric(series.astype(str).str.replace(r'[\$,]', '', regex=True), errors='coerce')
                if temp_numeric.notna().sum() > total_rows * 0.8:
                    inferred_type = "Float"
                else:
                    inferred_type = "Text"
            
            # Compute stats
            min_val = None
            max_val = None
            mean_val = None
            median_val = None
            std_dev_val = None
            
            try:
                # Clean and parse series if it was classified as Float/Integer but read as object
                clean_series = series
                if inferred_type in ["Integer", "Float"]:
                    if series.dtype == 'object':
                        clean_series = pd.to_numeric(series.astype(str).str.replace(r'[\$,]', '', regex=True), errors='coerce')
                    
                    # Convert stats to python types (float, etc.) to prevent numpy JSON serialization errors
                    if clean_series.nunique() > 0:
                        min_val = str(clean_series.min())
                        max_val = str(clean_series.max())
                        mean_val = float(clean_series.mean()) if not pd.isna(clean_series.mean()) else None
                        median_val = float(clean_series.median()) if not pd.isna(clean_series.median()) else None
                        std_dev_val = float(clean_series.std()) if not pd.isna(clean_series.std()) else None
                else:
                    # Non-numeric stats
                    if distinct_cnt > 0:
                        # Drop NA for min/max
                        non_null = series.dropna().astype(str)
                        if len(non_null) > 0:
                            min_val = str(non_null.min())[:100]
                            max_val = str(non_null.max())[:100]
            except Exception:
                pass # Fallback to None if statistics computation fails
                
            # Classify semantic type
            semantic_type = MetadataEngine.classify_semantic_type(col, inferred_type, distinct_cnt)
            
            profiles.append({
                "column_name": col,
                "data_type": inferred_type,
                "semantic_type": semantic_type,
                "null_percentage": round(null_pct, 2),
                "distinct_count": distinct_cnt,
                "cardinality": round(cardinality, 4),
                "min_value": min_val,
                "max_value": max_val,
                "mean_value": mean_val,
                "median_value": median_val,
                "std_dev_value": std_dev_val
            })
            
        return profiles

    @staticmethod
    def classify_semantic_type(col_name: str, data_type: str, distinct_count: int) -> str:
        name_lower = col_name.lower()
        
        # Rule 1: Regex rules matching column names
        for sem_type, pattern in SEMANTIC_RULES.items():
            if re.search(pattern, name_lower):
                # Ensure Boolean has low cardinality
                if sem_type == "Boolean" and distinct_count > 5:
                    continue
                return sem_type
                
        # Rule 2: Low distinct integers/texts can be Boolean or Categorical
        if data_type == "Boolean":
            return "Boolean"
        if distinct_count == 2:
            return "Boolean"
            
        # Default fallbacks
        if data_type in ["Integer", "Float"]:
            return "Number"
        elif data_type == "DateTime":
            return "Date"
            
        return "Text"

    @staticmethod
    def classify_dataset_domain(columns: List[Dict[str, Any]]) -> Tuple[str, float]:
        semantic_types = [c["semantic_type"] for c in columns]
        col_names_lower = [c["column_name"].lower() for c in columns]
        
        domain_scores = {
            "Retail": 0.0,
            "Healthcare": 0.0,
            "HR": 0.0,
            "Finance": 0.0,
            "Marketing": 0.0
        }
        
        # HR Score
        hr_keywords = ["salary", "wage", "employee", "staff", "attrition", "tenure", "hire", "department", "job", "role"]
        domain_scores["HR"] = sum(1 for kw in hr_keywords if any(kw in col for col in col_names_lower)) / len(hr_keywords)
        
        # Healthcare Score
        hc_keywords = ["patient", "admission", "diagnosis", "doctor", "hospital", "disease", "treatment", "recovery", "clinic"]
        domain_scores["Healthcare"] = sum(1 for kw in hc_keywords if any(kw in col for col in col_names_lower)) / len(hc_keywords)
        
        # Finance Score
        fin_keywords = ["asset", "liability", "expense", "balance", "capital", "portfolio", "credit", "debit", "equity", "cash"]
        domain_scores["Finance"] = sum(1 for kw in fin_keywords if any(kw in col for col in col_names_lower)) / len(fin_keywords)
        
        # Retail / E-Commerce Score
        retail_keywords = ["sku", "store", "order_number", "cart", "product", "sales", "transaction", "quantity", "return", "refund"]
        domain_scores["Retail"] = sum(1 for kw in retail_keywords if any(kw in col for col in col_names_lower)) / len(retail_keywords)
        
        # Marketing Score
        mkt_keywords = ["campaign", "lead", "click", "ctr", "impressions", "conversion", "roi", "ad_", "channel", "cost_per"]
        domain_scores["Marketing"] = sum(1 for kw in mkt_keywords if any(kw in col for col in col_names_lower)) / len(mkt_keywords)
        
        # Sort and select domain
        best_domain = max(domain_scores, key=domain_scores.get)
        best_score = domain_scores[best_domain] * 100
        
        if best_score < 30.0:
            return "Generic Business Dataset", 100.0
            
        return best_domain, round(best_score, 2)

    @staticmethod
    def suggest_kpis_and_charts(columns: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        kpis = []
        charts = []
        
        # Find key Measures (Numerical items to sum/avg)
        monetary_cols = [c["column_name"] for c in columns if c["semantic_type"] == "Monetary"]
        qty_cols = [c["column_name"] for c in columns if c["semantic_type"] == "Quantity"]
        pct_cols = [c["column_name"] for c in columns if c["semantic_type"] == "Percentage"]
        number_cols = [c["column_name"] for c in columns if c["semantic_type"] == "Number"]
        
        # Find Dimensions (for categories and groupings)
        date_cols = [c["column_name"] for c in columns if c["semantic_type"] == "Date"]
        geo_cols = [c["column_name"] for c in columns if c["semantic_type"] == "Geographic"]
        text_cols = [c["column_name"] for c in columns if c["semantic_type"] == "Text"]
        id_cols = [c["column_name"] for c in columns if "id" in c["column_name"].lower() or "code" in c["column_name"].lower()]
        
        # Suggest KPIs
        if monetary_cols:
            kpis.append({
                "name": f"Total {monetary_cols[0].replace('_', ' ').title()}",
                "formula": f"SUM({monetary_cols[0]})"
            })
            if len(monetary_cols) > 1:
                kpis.append({
                    "name": f"Total {monetary_cols[1].replace('_', ' ').title()}",
                    "formula": f"SUM({monetary_cols[1]})"
                })
        
        if qty_cols:
            kpis.append({
                "name": f"Total {qty_cols[0].replace('_', ' ').title()}",
                "formula": f"SUM({qty_cols[0]})"
            })
            
        if id_cols:
            kpis.append({
                "name": f"Total Records Volume",
                "formula": f"COUNT({id_cols[0]})"
            })
        else:
            kpis.append({
                "name": "Total Records Volume",
                "formula": "COUNT(*)"
            })
            
        if pct_cols:
            kpis.append({
                "name": f"Average {pct_cols[0].replace('_', ' ').title()}",
                "formula": f"AVG({pct_cols[0]})"
            })
            
        # Suggested Charts
        # Chart 1: Time Series (Date + Measure)
        measure_col = monetary_cols[0] if monetary_cols else (qty_cols[0] if qty_cols else (number_cols[0] if number_cols else None))
        if date_cols and measure_col:
            charts.append({
                "type": "Line Chart",
                "title": f"{measure_col.replace('_', ' ').title()} Over Time",
                "x_axis": date_cols[0],
                "y_axis": measure_col
            })
            
        # Chart 2: Category distribution (Text + Measure)
        cat_col = text_cols[0] if text_cols else (geo_cols[0] if geo_cols else None)
        if cat_col and measure_col:
            charts.append({
                "type": "Pie Chart",
                "title": f"{measure_col.replace('_', ' ').title()} Share by {cat_col.replace('_', ' ').title()}",
                "x_axis": cat_col,
                "y_axis": measure_col
            })
            charts.append({
                "type": "Bar Chart",
                "title": f"{measure_col.replace('_', ' ').title()} Distribution across {cat_col.replace('_', ' ').title()}",
                "x_axis": cat_col,
                "y_axis": measure_col
            })
            
        # Chart 3: Correlation (Measure + Measure)
        if len(number_cols) >= 2:
            charts.append({
                "type": "Scatter Plot",
                "title": f"Correlation between {number_cols[0]} and {number_cols[1]}",
                "x_axis": number_cols[0],
                "y_axis": number_cols[1]
            })
            
        # Standard fallback if no charts generated
        if not charts and columns:
            dimension = columns[0]["column_name"]
            measure = columns[-1]["column_name"]
            charts.append({
                "type": "Bar Chart",
                "title": f"Analysis of {measure} by {dimension}",
                "x_axis": dimension,
                "y_axis": measure
            })
            
        return kpis, charts
