import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_data():
    np.random.seed(42)
    rows = 150
    
    # Base lists
    store_options = [
        {"code": "ST001", "name": "Metro Center Store", "region": "North", "city": "Chicago", "state": "IL"},
        {"code": "ST002", "name": "Eastside Hub Store", "region": "East", "city": "New York", "state": "NY"},
        {"code": "ST003", "name": "West Coast Outpost", "region": "West", "city": "San Francisco", "state": "CA"},
        {"code": "ST004", "name": "Southern Plaza Store", "region": "South", "city": "Dallas", "state": "TX"}
    ]
    
    product_options = [
        {"sku": "SKU-ELEC-101", "name": "Quantum Pro Headset", "cat": "Electronics", "cost": 45.0, "insightflow": 89.99},
        {"sku": "SKU-ELEC-102", "name": "OptiView LED Monitor", "cat": "Electronics", "cost": 120.0, "insightflow": 249.99},
        {"sku": "SKU-APPL-201", "name": "AeroBreeze Smart Fan", "cat": "Appliances", "cost": 30.0, "insightflow": 59.99},
        {"sku": "SKU-FURN-301", "name": "ErgoComfort Desk Chair", "cat": "Furniture", "cost": 85.0, "insightflow": 179.99},
        {"sku": "SKU-CLOT-401", "name": "AeroWeave Sports Jacket", "cat": "Clothing", "cost": 15.0, "insightflow": 39.99}
    ]
    
    customer_options = [
        {"code": "CUST-001", "first": "Saurabh", "last": "Sahu"},
        {"code": "CUST-002", "first": "John", "last": "Doe"},
        {"code": "CUST-003", "first": "Alice", "last": "Smith"},
        {"code": "CUST-004", "first": "Bob", "last": "Johnson"},
        {"code": "CUST-005", "first": "Emma", "last": "Davis"}
    ]
    
    data = []
    base_date = datetime.now() - timedelta(days=60)
    
    for i in range(rows):
        # Determine order
        order_num = f"ORD-{1000 + i // 2}" # Some multiple items per order
        order_date = (base_date + timedelta(days=i // 3)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Select entities
        store = store_options[np.random.randint(len(store_options))]
        prod = product_options[np.random.randint(len(product_options))]
        cust = customer_options[np.random.randint(len(customer_options))]
        
        qty = np.random.randint(1, 6)
        # Introduce currency formatting and anomalies
        unit_price = f"${prod['insightflow']}" if np.random.rand() > 0.1 else prod['insightflow']
        cost_price = prod['cost']
        insightflow_price = prod['insightflow']
        
        row = {
            "order_number": order_num,
            "order_date": order_date,
            "store_code": store["code"],
            "store_name": store["name"],
            "region": store["region"],
            "city": store["city"],
            "state": store["state"],
            "customer_code": cust["code"],
            "customer_first_name": cust["first"],
            "customer_last_name": cust["last"],
            "sku": prod["sku"],
            "product_name": prod["name"],
            "category_name": prod["cat"],
            "quantity": qty,
            "unit_price": unit_price,
            "cost_price": cost_price,
            "insightflow_price": insightflow_price,
            "payment_method": np.random.choice(["Credit Card", "PayPal", "Apple Pay", "Cash"]),
            "payment_status": "Success",
            "refund_quantity": 0,
            "refund_amount": 0.0,
            "return_reason": ""
        }
        
        # Add outlier (IQR check target)
        if i == 42:
            row["quantity"] = 150 # Outlier quantity
            row["unit_price"] = "$999.99"
        
        # Add missing cell
        if i == 15:
            row["category_name"] = np.nan # Mode imputation target
            
        if i == 50:
            row["quantity"] = np.nan # Median imputation target
            
        data.append(row)
        
    df = pd.DataFrame(data)
    
    # Add duplicate rows
    df = pd.concat([df, df.iloc[10:15]], ignore_index=True)
    
    # Save
    df.to_csv("../insightflow_sample.csv", index=False)
    print(f"Sample dataset containing {len(df)} rows written to insightflow_sample.csv")

if __name__ == "__main__":
    generate_data()
