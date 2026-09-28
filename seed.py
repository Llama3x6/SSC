"""
seed.py — Populates the Sentient Supply Chain ERP with realistic demo data.

Run with: python seed.py
Requires: server running at http://127.0.0.1:8000
Order: suppliers → products → supplier_product relations → orders
"""

import sys
from datetime import date, timedelta

import requests

BASE_URL = "http://127.0.0.1:8000"

def days_from_today(n: int) -> str:
    """Return an ISO date n days from today.

    Seed data must stay valid whenever the script runs — the service layer
    rejects contracts already expired, so absolute dates eventually break the seed.
    """
    return (date.today() + timedelta(days=n)).isoformat()

def post(endpoint: str, payload: dict) -> dict:
    resp = requests.post(f"{BASE_URL}{endpoint}", json=payload)
    if resp.status_code not in (200, 201):
        print(f"  ❌ FAILED {endpoint}: {resp.status_code} — {resp.text}")
        sys.exit(1)
    data = resp.json()
    print(f"  ✅ {endpoint} → {data}")
    return data


# ── 1. Suppliers ─────────────────────────────────────────────────────────────

print("\n── Seeding Suppliers ──")

s1 = post(
    "/suppliers",
    {
        "name": "AlphaComponents AG",
        "country": "DE",
        "reliability_score": 0.95,
        "contract_valid_until": days_from_today(365),
    },
)

s2 = post(
    "/suppliers",
    {
        "name": "BetaParts GmbH",
        "country": "TW",
        "reliability_score": 0.80,
        "contract_valid_until": days_from_today(270),
    },
)

s3 = post(
    "/suppliers",
    {
        "name": "GammaSourcing Ltd",
        "country": "CN",
        "reliability_score": 0.72,
        "contract_valid_until": days_from_today(20),
    },
)


# ── 2. Products ───────────────────────────────────────────────────────────────

print("\n── Seeding Products ──")

p1 = post(
    "/products",
    {
        "sku": "ELC-100001",
        "name": "Capacitor 100uF",
        "current_stock": 8,  # below threshold → triggers reorder
        "reorder_threshold": 50,
    },
)

p2 = post(
    "/products",
    {
        "sku": "ELC-100002",
        "name": "Resistor 10kΩ",
        "current_stock": 200,
        "reorder_threshold": 100,
    },
)

p3 = post(
    "/products",
    {
        "sku": "MEC-200001",
        "name": "Steel Bracket M8",
        "current_stock": 12,  # below threshold → triggers reorder
        "reorder_threshold": 75,
    },
)

p4 = post(
    "/products",
    {
        "sku": "MEC-200002",
        "name": "Hex Bolt M6x20",
        "current_stock": 500,
        "reorder_threshold": 200,
    },
)


# ── 3. Supplier–Product Relations ─────────────────────────────────────────────

print("\n── Seeding Supplier–Product Relations ──")

# AlphaComponents supplies both electronic parts
post("/supplier-product/", {"supplier_id": s1["id"], "sku": p1["sku"]})
post("/supplier-product/", {"supplier_id": s1["id"], "sku": p2["sku"]})

# BetaParts also supplies the capacitor (competitor — lower reliability)
post("/supplier-product/", {"supplier_id": s2["id"], "sku": p1["sku"]})

# BetaParts and GammaSourcing supply mechanical parts
post("/supplier-product/", {"supplier_id": s2["id"], "sku": p3["sku"]})
post("/supplier-product/", {"supplier_id": s2["id"], "sku": p4["sku"]})
post("/supplier-product/", {"supplier_id": s3["id"], "sku": p3["sku"]})
post("/supplier-product/", {"supplier_id": s3["id"], "sku": p4["sku"]})


# ── 4. Orders ─────────────────────────────────────────────────────────────────

print("\n── Seeding Orders ──")

# A confirmed order for the capacitor via AlphaComponents
post(
    "/orders",
    {
        "product_sku": p1["sku"],
        "supplier_id": s1["id"],
        "quantity": 200,
        "status": "confirmed",
    },
)

# A shipped order for resistors via AlphaComponents
post(
    "/orders",
    {
        "product_sku": p2["sku"],
        "supplier_id": s1["id"],
        "quantity": 500,
        "status": "shipped",
    },
)

# A drafted order for steel brackets via BetaParts
post(
    "/orders",
    {
        "product_sku": p3["sku"],
        "supplier_id": s2["id"],
        "quantity": 300,
        "status": "drafted",
    },
)


print("\n✅ Seed complete.\n")
