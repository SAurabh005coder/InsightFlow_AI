from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user: Dict[str, Any]

class TokenData(BaseModel):
    user_id: Optional[str] = None

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: str
    role_name: str  # CEO, Store_Manager, Sales_Manager, Data_Analyst

class UserResponse(UserBase):
    user_id: UUID
    role_name: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Dashboard KPIs
class KPISummary(BaseModel):
    revenue: float
    profit: float
    margin: float
    orders: int
    customers: int
    inventory_count: int
    revenue_growth: float  # Percentage
    profit_growth: float   # Percentage
    avg_order_value: float
    return_rate: float
    stockout_rate: float
    repeat_purchase_rate: float

class DashboardData(BaseModel):
    kpis: KPISummary
    revenue_trend: List[Dict[str, Any]]
    category_split: List[Dict[str, Any]]
    store_performance: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    ai_insights: List[str]

# Data Cleaning / Upload
class UploadReport(BaseModel):
    upload_id: UUID
    filename: str
    status: str
    total_records: int
    processed_records: int
    null_report: Dict[str, float]
    duplicates_removed: int
    outliers_detected: int
    cleaning_time_seconds: float
    domain: Optional[str] = None
    confidence_score: Optional[float] = None
    columns: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[str]] = None

# Product schemas
class ProductBase(BaseModel):
    sku: str
    product_name: str
    cost_price: float
    insightflow_price: float

class ProductResponse(ProductBase):
    product_id: UUID
    category_name: str

    model_config = ConfigDict(from_attributes=True)

# Forecasting schemas
class ForecastPoint(BaseModel):
    date: str
    historical: Optional[float] = None
    forecast: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None

class ForecastResponse(BaseModel):
    metric: str  # Revenue or Demand
    forecast: List[ForecastPoint]
    mape: float  # Mean Absolute Percentage Error (accuracy metric)

# Customer Segment
class CustomerSegmentPoint(BaseModel):
    customer_id: str
    customer_code: str
    name: str
    recency: int
    frequency: int
    monetary: float
    segment: str

class SegmentSummary(BaseModel):
    segment_name: str
    customer_count: int
    avg_monetary: float
    percentage: float

# Metadata-Driven schemas
class ColumnMetadataResponse(BaseModel):
    column_name: str
    data_type: str
    semantic_type: str
    null_percentage: float
    distinct_count: int
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_dev_value: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class DatasetResponse(BaseModel):
    dataset_id: UUID
    filename: str
    domain: str
    confidence_score: float
    record_count: int
    created_at: datetime
    columns: List[ColumnMetadataResponse]

    model_config = ConfigDict(from_attributes=True)

class DynamicKPI(BaseModel):
    name: str
    value: str
    formula: str

class DynamicChart(BaseModel):
    type: str
    title: str
    x_axis: str
    y_axis: str
    data: List[Dict[str, Any]]

class DynamicDashboardResponse(BaseModel):
    dataset_id: UUID
    filename: str
    domain: str
    confidence_score: float
    record_count: int
    kpis: List[DynamicKPI]
    charts: List[DynamicChart]
    insights: List[str]
