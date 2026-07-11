import json
import uuid
from sqlalchemy.orm import Session
from app.models.models import Dataset, ColumnMetadata
from app.services.analytics import AnalyticsService
from app.services.ml import MLService
from typing import Dict, Any, Optional

class ContextBuilder:
    @staticmethod
    def build_context(db: Session, dataset_id: Optional[str], user_id: str) -> str:
        if not dataset_id:
            return "CONTEXT: No active dataset is currently selected or uploaded by the user. Instruct the user to upload a dataset or select an existing one to begin analytical queries."
            
        try:
            dataset_uuid = uuid.UUID(str(dataset_id))
        except (ValueError, TypeError):
            return "CONTEXT: Invalid dataset ID format."

        # Fetch basic dataset details
        dataset = db.query(Dataset).filter(Dataset.dataset_id == dataset_uuid).first()
        if not dataset:
            return f"CONTEXT: Dataset with ID {dataset_id} was not found."

        # 1. Gather column metadata
        columns = db.query(ColumnMetadata).filter(ColumnMetadata.dataset_id == dataset_uuid).all()
        schema_info = []
        for col in columns:
            stats = []
            if col.mean_value is not None: stats.append(f"Mean: {float(col.mean_value):.2f}")
            if col.median_value is not None: stats.append(f"Median: {float(col.median_value):.2f}")
            if col.distinct_count is not None: stats.append(f"Distinct values: {col.distinct_count}")
            if col.null_percentage is not None: stats.append(f"Nulls: {float(col.null_percentage):.1f}%")
            stats_str = f" ({', '.join(stats)})" if stats else ""
            schema_info.append(f"- Column '{col.column_name}': Type={col.data_type}, Semantic={col.semantic_type}{stats_str}")

        # 2. Gather Dashboard data (KPIs, Charts data, Insights)
        try:
            db_summary = AnalyticsService.get_dashboard_summary(db, dataset_id=str(dataset_uuid), user_id=user_id)
        except Exception as e:
            db_summary = {"kpis": [], "charts": [], "insights": [f"Error compiling dashboard metrics: {str(e)}"]}

        kpis_context = []
        for kpi in db_summary.get("kpis", []):
            kpis_context.append(f"- {kpi['name']}: {kpi['value']} (Formula: {kpi['formula']})")

        charts_context = []
        for chart in db_summary.get("charts", []):
            chart_type = chart.get("type", "Chart")
            chart_title = chart.get("title", "Metric Split")
            chart_data = chart.get("data", [])
            data_summary = [f"{d.get('name', d.get('date', 'N/A'))}: {d.get('value', 0)}" for d in chart_data[:5]]
            charts_context.append(f"- {chart_type} '{chart_title}': Top values -> {', '.join(data_summary)}")

        insights_context = [f"- {insight}" for insight in db_summary.get("insights", [])]

        # 3. Gather ML Forecasting
        try:
            forecast_data = MLService.forecast_sales(db, str(dataset_uuid), days_ahead=30)
            mape = forecast_data.get("mape", 0.0)
            metric_name = forecast_data.get("metric", "Sales")
            forecast_points = forecast_data.get("forecast", [])
            
            # Summarize forecast values
            historical_points = [p.get("historical", 0.0) for p in forecast_points if "historical" in p and p.get("historical") is not None]
            future_points = [p.get("forecast", 0.0) for p in forecast_points if "forecast" in p and p.get("forecast") is not None]
            
            forecast_summary = (
                f"- Forecast Target Metric: {metric_name}\n"
                f"- Forecast Accuracy (MAPE): {mape}%\n"
                f"- Historical Data Count: {len(historical_points)} records\n"
                f"- Average Historical Value: {sum(historical_points)/len(historical_points):,.2f}\n" if historical_points else "- No historical metrics parsed.\n"
            )
            if future_points:
                forecast_summary += (
                    f"- 30-Day Forecast Point Count: {len(future_points)} days\n"
                    f"- Total Forecasted Sum: ${sum(future_points):,.2f}\n"
                    f"- Average Projected Day: ${sum(future_points)/len(future_points):,.2f}\n"
                    f"- Projected Min: ${min(future_points):,.2f}, Projected Max: ${max(future_points):,.2f}"
                )
        except Exception as e:
            forecast_summary = f"- Forecasting analysis failed or is unavailable: {str(e)}"

        # 4. Gather Customer Segmentation (K-Means)
        try:
            segment_data = MLService.segment_customers(db, str(dataset_uuid))
            summary_points = segment_data.get("summary", [])
            segment_context = []
            for seg in summary_points:
                segment_context.append(
                    f"- Segment '{seg['segment_name']}': Count={seg['customer_count']} customers ({seg['percentage']}% of total), Average Spend/Monetary=${seg['avg_monetary']:,.2f}"
                )
            segment_summary = "\n".join(segment_context) if segment_context else "- Customer segment clusters are unassigned."
        except Exception as e:
            segment_summary = f"- Customer RFM clustering analysis is unavailable: {str(e)}"

        # Compile everything together
        context_string = f"""=== DATASET INFORMATION ===
File Name: {dataset.filename}
Ingested Domain: {dataset.domain}
Record Count: {dataset.record_count}
Metadata Confidence Score: {float(dataset.confidence_score):.1f}%

=== METADATA & SCHEMA ===
{chr(10).join(schema_info)}

=== DASHBOARD KPIS & CALCULATIONS ===
{chr(10).join(kpis_context) if kpis_context else "- No computed KPIs exist."}

=== DASHBOARD VISUALIZATIONS & RANKS ===
{chr(10).join(charts_context) if charts_context else "- No charts data exist."}

=== RULE-BASED INSIGHTS & SKEWNESS ===
{chr(10).join(insights_context) if insights_context else "- No insights exist."}

=== DEMAND FORECAST (ML Holt-Winters & OLS Exponents) ===
{forecast_summary}

=== CUSTOMER SEGMENTATION (ML K-Means Clustering) ===
{segment_summary}
"""
        return context_string
