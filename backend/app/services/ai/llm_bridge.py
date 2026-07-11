import logging
import httpx
from app.core.config import settings
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class LLMBridge:
    @staticmethod
    def invoke(messages: List[Dict[str, str]], context_data: str) -> str:
        provider = settings.AI_PROVIDER.lower() if settings.AI_PROVIDER else "mock"
        
        if provider == "openai" and settings.OPENAI_API_KEY:
            try:
                response = LLMBridge._call_openai(messages)
                if response:
                    return response
            except Exception as e:
                logger.error(f"OpenAI invocation failed, falling back to mock: {e}")
                
        elif provider == "gemini" and settings.GEMINI_API_KEY:
            try:
                response = LLMBridge._call_gemini(messages)
                if response:
                    return response
            except Exception as e:
                logger.error(f"Gemini invocation failed, falling back to mock: {e}")

        # Fallback to local rule-based mock interpreter
        user_query = messages[-1]["content"] if messages else ""
        return LLMBridge._call_mock(user_query, context_data)

    @staticmethod
    def _call_openai(messages: List[Dict[str, str]]) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.1
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"].strip()

    @staticmethod
    def _call_gemini(messages: List[Dict[str, str]]) -> str:
        # Extract system instruction
        system_instruction = ""
        contents = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_instruction = content
            elif role == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
            elif role in ["assistant", "model"]:
                contents.append({
                    "role": "model",
                    "parts": [{"text": content}]
                })
                
        # Alternating check: Gemini requires user-model alternating. If consecutive roles occur, merge them
        cleaned_contents = []
        for i, item in enumerate(contents):
            if i == 0:
                cleaned_contents.append(item)
            else:
                last_item = cleaned_contents[-1]
                if last_item["role"] == item["role"]:
                    # Merge consecutive text parts
                    last_item["parts"][0]["text"] += "\n" + item["parts"][0]["text"]
                else:
                    cleaned_contents.append(item)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": cleaned_contents,
            "generationConfig": {
                "temperature": 0.1
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
            
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            res_json = response.json()
            try:
                return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
            except (KeyError, IndexError) as e:
                raise ValueError(f"Unexpected response structure from Gemini API: {res_json}")

    @staticmethod
    def _call_mock(query: str, context: str) -> str:
        query_lower = query.lower()
        
        # Check if context states no dataset is loaded
        if "No active dataset is currently selected" in context or "No business datasets uploaded yet" in context:
            return "I cannot find that information in the analytical results. Please upload a dataset to begin."

        # Parse sections of the context to answer grounded queries
        lines = context.split("\n")
        
        # 1. Executive Summary
        if any(w in query_lower for w in ["summary", "executive", "describe", "overview", "about"]):
            filename = "Unknown"
            domain = "Unknown"
            records = "0"
            for line in lines:
                if line.startswith("File Name:"): filename = line.split(":", 1)[1].strip()
                if line.startswith("Ingested Domain:"): domain = line.split(":", 1)[1].strip()
                if line.startswith("Record Count:"): records = line.split(":", 1)[1].strip()
            
            insights = []
            capture_insights = False
            for line in lines:
                if line.startswith("=== RULE-BASED INSIGHTS"):
                    capture_insights = True
                    continue
                if capture_insights:
                    if line.startswith("==="):
                        break
                    if line.strip().startswith("-"):
                        insights.append(line.strip())
            insights_str = "\n".join(insights) if insights else "- No operational insights computed."
            
            return f"""### Executive Dataset Summary
- **Dataset Filename:** {filename}
- **Identified Domain:** {domain}
- **Total Record Count:** {records} records

#### Computational Insights:
{insights_str}"""

        # 2. KPIs / Sales / Revenue / Margins
        if any(w in query_lower for w in ["kpi", "revenue", "profit", "margin", "sales", "order", "value", "cost"]):
            kpis = []
            capture_kpis = False
            for line in lines:
                if line.startswith("=== DASHBOARD KPIS"):
                    capture_kpis = True
                    continue
                if capture_kpis:
                    if line.startswith("==="):
                        break
                    if line.strip().startswith("-"):
                        kpis.append(line.strip())
            kpis_str = "\n".join(kpis) if kpis else "- No computed KPIs are present."
            return f"""### Dashboard KPIs Interpretation
Here are the pre-calculated KPIs for the active dataset:
{kpis_str}

*All values represent exact queries calculated from the DuckDB analytical layer.*"""

        # 3. Forecast / Predictions / Future / Trend
        if any(w in query_lower for w in ["forecast", "prediction", "future", "trend", "predict"]):
            forecast_lines = []
            capture_forecast = False
            for line in lines:
                if line.startswith("=== DEMAND FORECAST"):
                    capture_forecast = True
                    continue
                if capture_forecast:
                    if line.startswith("==="):
                        break
                    if line.strip():
                        forecast_lines.append(line.strip())
            forecast_str = "\n".join(forecast_lines) if forecast_lines else "- Forecasting metrics are unavailable."
            return f"""### Machine Learning Sales Forecast (30-Day Outlook)
Based on the Exponential Smoothing (Holt-Winters) and OLS linear calculations, here is the forecasting breakdown:
{forecast_str}

*This forecast assumes baseline seasonal patterns and residuals fitted from the historic Point-of-Sale logs.*"""

        # 4. Segmentation / Customers / Groups / Clusters
        if any(w in query_lower for w in ["segment", "customer", "group", "cluster", "rfm", "kmeans"]):
            segment_lines = []
            capture_segments = False
            for line in lines:
                if line.startswith("=== CUSTOMER SEGMENTATION"):
                    capture_segments = True
                    continue
                if capture_segments:
                    if line.startswith("==="):
                        break
                    if line.strip():
                        segment_lines.append(line.strip())
            segment_str = "\n".join(segment_lines) if segment_lines else "- Customer segment groups are not computed."
            return f"""### Customer RFM Segmentation Summary
The K-Means clustering algorithm partitioned the customer base into distinct cohorts based on Recency, Frequency, and Monetary parameters:
{segment_str}

*These cohorts represent statistical distributions. Do not calculate additional segments.*"""

        # 5. Fallback for out-of-scope / calculations / missing context
        return "I cannot find that information in the analytical results."
