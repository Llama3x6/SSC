"""
conftest.py — Test configuration for the Sentient Supply Chain ERP.

Sets DATABASE_URL to an isolated test database BEFORE any app module is
imported. This is the critical ordering requirement: os.environ must be
mutated before SQLAlchemy's engine is instantiated at import time.
"""

import os

os.environ["DATABASE_URL"] = "sqlite:///./test_ssc.db"

import pytest
from fastapi.testclient import TestClient

from database import Base, engine
from main import app


# ── Database lifecycle ────────────────────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once for the test session, drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_ssc.db"):
        os.remove("test_ssc.db")


# ── HTTP client ───────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def client(setup_test_db):
    """Single TestClient instance for the session — no live server needed."""
    with TestClient(app) as c:
        yield c


# ── Resource fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def supplier(client):
    data = {
        "name": "Fixture Supplier",
        "reliability_score": 0.90,
        "contract_valid_until": "2027-12-31",
    }
    resp = client.post("/suppliers/", json=data)
    assert resp.status_code == 201, f"Supplier fixture failed: {resp.text}"
    s = resp.json()
    yield s
    client.delete(f"/suppliers/{s['id']}")


@pytest.fixture
def product(client):
    data = {
        "sku": "TST-100001",
        "name": "Fixture Product",
        "current_stock": 100,
        "reorder_threshold": 20,
    }
    resp = client.post("/products/", json=data)
    assert resp.status_code == 201, f"Product fixture failed: {resp.text}"
    p = resp.json()
    yield p
    client.delete(f"/products/{p['sku']}")


@pytest.fixture
def supplier_product(client, supplier, product):
    """Creates the supplier-product relation required before order creation."""
    data = {"supplier_id": supplier["id"], "sku": product["sku"]}
    resp = client.post("/supplier-product/", json=data)
    assert resp.status_code == 201, f"SupplierProduct fixture failed: {resp.text}"
    yield resp.json()
    client.delete(f"/supplier-product/{supplier['id']}/{product['sku']}")


@pytest.fixture
def order(client, supplier_product, supplier, product):
    data = {
        "product_sku": product["sku"],
        "supplier_id": supplier["id"],
        "quantity": 5,
        "status": "drafted",
    }
    resp = client.post("/orders/", json=data)
    assert resp.status_code == 201, f"Order fixture failed: {resp.text}"
    o = resp.json()
    yield o
    client.delete(f"/orders/{o['id']}")
