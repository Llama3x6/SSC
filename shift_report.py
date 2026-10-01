# shift_report.py
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

from llm import call_llm_structured
from models import ShiftReport

load_dotenv()

BASE_URL = "http://localhost:8000"
LOOKBACK_DAYS = 2
REPORT_FILE = "shift_report.txt"

# (connect, read) seconds for the local ERP.
ERP_TIMEOUT = (5, 15)


def fetch_data() -> dict:
    today = date.today()
    start_date = today - timedelta(days=LOOKBACK_DAYS)

    # Recent orders via date filter
    orders = requests.get(
        f"{BASE_URL}/orders",
        params={"from_date": start_date.isoformat()},
        timeout=ERP_TIMEOUT,
    ).json()

    # Suppliers involved in recent orders
    supplier_ids = {o["supplier_id"] for o in orders}
    active_suppliers = [
        requests.get(f"{BASE_URL}/suppliers/{sid}", timeout=ERP_TIMEOUT).json()
        for sid in supplier_ids
    ]

    # Products below reorder threshold
    products = requests.get(f"{BASE_URL}/products", timeout=ERP_TIMEOUT).json()
    reorder_candidates = [
        p for p in products if p["current_stock"] <= p["reorder_threshold"]
    ]

    # Suppliers with contracts expiring within 31 days
    all_suppliers = requests.get(f"{BASE_URL}/suppliers", timeout=ERP_TIMEOUT).json()
    expiry_threshold = (today + timedelta(days=31)).isoformat()
    expiring_contracts = [
        s for s in all_suppliers if s["contract_valid_until"] <= expiry_threshold
    ]

    return {
        "orders": orders,
        "active_suppliers": active_suppliers,
        "reorder_candidates": reorder_candidates,
        "expiring_contracts": expiring_contracts,
    }


def build_prompt(data: dict) -> str:
    # format data into a structured prompt
    prompt = (
        "You are a supply chain assistant generating a concise shift report for an operations manager. "
        "Summarize the following ERP data clearly. Flag anything that needs attention. Be brief.\n\n"
    )
    prompt += "Shift Report\n\n"
    prompt += f"Recent orders (last {LOOKBACK_DAYS} days):\n"
    for order in data["orders"]:
        prompt += f"- {order['order_date']}: SKU {order['product_sku']}, qty {order['quantity']}, status {order['status']}, supplier_id {order['supplier_id']}\n"
    prompt += "\nActive suppliers:\n"
    for supplier in data["active_suppliers"]:
        prompt += f"- {supplier['name']}\n"
    prompt += "\nProducts below reorder threshold:\n"
    for product in data["reorder_candidates"]:
        prompt += f"- {product['name']}: {product['current_stock']} (reorder threshold: {product['reorder_threshold']})\n"
    prompt += "\nSuppliers with expiring contracts:\n"
    for supplier in data["expiring_contracts"]:
        prompt += f"- {supplier['name']}: contract expires {supplier['contract_valid_until']}\n"
    return prompt


def run_report():
    data = fetch_data()
    prompt = build_prompt(data)
    prompt += "\nProvide a structured shift report with clear sections and alerts."

    # Get structured output
    report = call_llm_structured(prompt, ShiftReport)

    # Format for output
    formatted = f"""Generated: {report.timestamp}

SHIFT REPORT
============

{report.summary}

"""

    for section in report.sections:
        formatted += f"\n{section.category.upper()}:\n"
        for item in section.items:
            formatted += f"  • {item}\n"

    if report.alerts:
        formatted += f"\nALERTS (Urgent):\n"
        for alert in report.alerts:
            formatted += f"  ⚠ {alert}\n"

    with open(REPORT_FILE, "w") as f:
        f.write(formatted)
    print(formatted)


if __name__ == "__main__":
    run_report()
