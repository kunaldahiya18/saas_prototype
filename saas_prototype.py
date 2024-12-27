# SaaS Prototype: OMS-WMS-Courier Integration
# Tech Stack: FastAPI (Backend), SQLite (Database), Mock APIs for Courier Integration

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3

# Initialize FastAPI app
app = FastAPI()

# Database setup
conn = sqlite3.connect('saas_prototype.db', check_same_thread=False)
cursor = conn.cursor()

# Create database tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    destination TEXT,
    weight REAL,
    courier TEXT,
    status TEXT DEFAULT 'Pending'
)
''')

conn.commit()

# Models
class Order(BaseModel):
    customer_name: str
    destination: str
    weight: float
    courier: Optional[str] = None

class AllocationRule(BaseModel):
    courier: str
    max_weight: float
    region: str

# Mock data for allocation rules
allocation_rules = [
    {"courier": "BlueDart", "max_weight": 10.0, "region": "Metro"},
    {"courier": "Delhivery", "max_weight": 20.0, "region": "Urban"},
    {"courier": "IndiaPost", "max_weight": 50.0, "region": "Rural"}
]

# Routes

@app.post("/orders/", response_model=dict)
def create_order(order: Order):
    # Determine courier based on rules
    courier = None
    for rule in allocation_rules:
        if order.weight <= rule['max_weight'] and rule['region'] in order.destination:
            courier = rule['courier']
            break

    if not courier:
        raise HTTPException(status_code=400, detail="No suitable courier found for the order.")

    # Insert order into database
    cursor.execute(
        "INSERT INTO orders (customer_name, destination, weight, courier) VALUES (?, ?, ?, ?)",
        (order.customer_name, order.destination, order.weight, courier)
    )
    conn.commit()

    return {"message": "Order created successfully", "courier": courier}

@app.get("/orders/", response_model=List[dict])
def list_orders():
    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()
    return [
        {
            "id": row[0],
            "customer_name": row[1],
            "destination": row[2],
            "weight": row[3],
            "courier": row[4],
            "status": row[5]
        }
        for row in rows
    ]

@app.get("/courier-rules/", response_model=List[AllocationRule])
def get_rules():
    return allocation_rules

@app.put("/orders/{order_id}/status")
def update_order_status(order_id: int, status: str):
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    return {"message": "Order status updated successfully"}

# Example of running the app
# To run: uvicorn saas_prototype:app --reload
# To test: Use Postman or a browser to interact with endpoints

# Heroku deployment setup
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

