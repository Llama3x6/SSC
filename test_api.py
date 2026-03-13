"""
test_api.py — Integration test suite for the Sentient Supply Chain ERP API.

Requirements:
  - Server must be running: uvicorn main:app --reload
  - Run with: pytest test_api.py -v

Design:
  - Each test is isolated: fixtures handle setup and teardown.
  - No test depends on the side effects of another.
  - Safe to run multiple times against a persistent database.
"""

import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"

# ================================================================================
# Fixtures
# ================================================================================

@pytest.fixture
def product():
    """Create a product before the test, delete it after."""
    data = {
        "sku": "TST-100001",
        "name": "Test Product",
        "current_stock": 100,
        "reorder_threshold": 20,
    }
    resp = requests.post(f"{BASE_URL}/products", json=data)
    assert resp.status_code == 201, f"Fixture setup failed: {resp.text}"
    yield resp.json()
    requests.delete(f"{BASE_URL}/products/{data['sku']}")


@pytest.fixture
def order(product):
    """Create an order referencing the product fixture, delete it after."""
    data = {
        "product_sku": product["sku"],
        "quantity": 5,
        "status": "drafted",
    }
    resp = requests.post(f"{BASE_URL}/orders", json=data)
    assert resp.status_code == 201, f"Fixture setup failed: {resp.text}"
    yield resp.json()
    requests.delete(f"{BASE_URL}/orders/{resp.json()['id']}")


@pytest.fixture
def supplier():
    """Create a supplier before the test, delete it after."""
    data = {
        "name": "Test Supplier",
        "reliability_score": 0.85,
        "contract_valid_until": "2027-12-31",
    }
    resp = requests.post(f"{BASE_URL}/suppliers", json=data)
    assert resp.status_code == 201, f"Fixture setup failed: {resp.text}"
    yield resp.json()
    requests.delete(f"{BASE_URL}/suppliers/{resp.json()['id']}")


# ================================================================================
# Product Tests
# ================================================================================

class TestProducts:

    def test_list_products(self):
        resp = requests.get(f"{BASE_URL}/products")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_product(self, product):
        assert product["sku"] == "TST-100001"
        assert product["name"] == "Test Product"
        assert product["current_stock"] == 100

    def test_create_duplicate_product(self, product):
        data = {
            "sku": "TST-100001",
            "name": "Duplicate",
            "current_stock": 10,
            "reorder_threshold": 5,
        }
        resp = requests.post(f"{BASE_URL}/products", json=data)
        assert resp.status_code == 409

    def test_get_product(self, product):
        resp = requests.get(f"{BASE_URL}/products/{product['sku']}")
        assert resp.status_code == 200
        assert resp.json()["sku"] == product["sku"]

    def test_get_nonexistent_product(self):
        resp = requests.get(f"{BASE_URL}/products/XXX-000000")
        assert resp.status_code == 404

    def test_update_product(self, product):
        updated = product.copy()
        updated["name"] = "Updated Product"
        updated["current_stock"] = 200
        resp = requests.put(f"{BASE_URL}/products/{product['sku']}", json=updated)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Product"
        assert resp.json()["current_stock"] == 200

    def test_update_product_sku_mismatch(self, product):
        updated = product.copy()
        resp = requests.put(f"{BASE_URL}/products/ZZZ-999999", json=updated)
        assert resp.status_code == 400

    def test_delete_product(self, product):
        resp = requests.delete(f"{BASE_URL}/products/{product['sku']}")
        assert resp.status_code == 204
        resp = requests.get(f"{BASE_URL}/products/{product['sku']}")
        assert resp.status_code == 404

    def test_delete_product_with_existing_order(self, product, order):
        """Product referenced by an order cannot be deleted."""
        resp = requests.delete(f"{BASE_URL}/products/{product['sku']}")
        assert resp.status_code == 409
        # Cleanup: order fixture teardown runs first, then product fixture teardown


# ================================================================================
# Supplier Tests
# ================================================================================

class TestSuppliers:

    def test_list_suppliers(self):
        resp = requests.get(f"{BASE_URL}/suppliers")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_supplier(self, supplier):
        assert supplier["name"] == "Test Supplier"
        assert supplier["reliability_score"] == 0.85

    def test_get_supplier(self, supplier):
        resp = requests.get(f"{BASE_URL}/suppliers/{supplier['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == supplier["id"]

    def test_get_nonexistent_supplier(self):
        resp = requests.get(f"{BASE_URL}/suppliers/999999")
        assert resp.status_code == 404

    def test_update_supplier(self, supplier):
        updated = supplier.copy()
        updated["name"] = "Updated Supplier"
        updated["reliability_score"] = 0.95
        resp = requests.put(f"{BASE_URL}/suppliers/{supplier['id']}", json=updated)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Supplier"

    def test_update_supplier_id_mismatch(self, supplier):
        updated = supplier.copy()
        resp = requests.put(f"{BASE_URL}/suppliers/999999", json=updated)
        assert resp.status_code == 400

    def test_delete_supplier(self, supplier):
        resp = requests.delete(f"{BASE_URL}/suppliers/{supplier['id']}")
        assert resp.status_code == 204
        resp = requests.get(f"{BASE_URL}/suppliers/{supplier['id']}")
        assert resp.status_code == 404

    def test_create_supplier_expired_contract(self):
        data = {
            "name": "Expired Supplier",
            "reliability_score": 0.5,
            "contract_valid_until": "2020-01-01",
        }
        resp = requests.post(f"{BASE_URL}/suppliers", json=data)
        assert resp.status_code == 400


# ================================================================================
# Order Tests
# ================================================================================

class TestOrders:

    def test_list_orders(self):
        resp = requests.get(f"{BASE_URL}/orders")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_order(self, order):
        assert order["product_sku"] is not None
        assert order["status"] == "drafted"

    def test_create_order_nonexistent_product(self):
        data = {"product_sku": "BAD-SKU", "quantity": 5, "status": "drafted"}
        resp = requests.post(f"{BASE_URL}/orders", json=data)
        assert resp.status_code == 404

    def test_get_order(self, order):
        resp = requests.get(f"{BASE_URL}/orders/{order['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == order["id"]

    def test_get_nonexistent_order(self):
        resp = requests.get(f"{BASE_URL}/orders/999999")
        assert resp.status_code == 404

    def test_update_order(self, order, product):
        updated = {
            "id": order["id"],
            "product_sku": product["sku"],
            "quantity": 10,
            "status": "drafted",
            "order_date": "2026-03-13",
        }
        resp = requests.put(f"{BASE_URL}/orders/{order['id']}", json=updated)
        assert resp.status_code == 200
        assert resp.json()["quantity"] == 10

    def test_delete_order(self, order):
        resp = requests.delete(f"{BASE_URL}/orders/{order['id']}")
        assert resp.status_code == 204
        resp = requests.get(f"{BASE_URL}/orders/{order['id']}")
        assert resp.status_code == 404

    def test_status_transition_drafted_to_confirmed(self, order):
        resp = requests.patch(f"{BASE_URL}/orders/{order['id']}/status?new_status=confirmed")
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"

    def test_status_transition_invalid(self, order):
        # Move to shipped first via confirmed
        requests.patch(f"{BASE_URL}/orders/{order['id']}/status?new_status=confirmed")
        requests.patch(f"{BASE_URL}/orders/{order['id']}/status?new_status=shipped")
        # Now try to go backwards
        resp = requests.patch(f"{BASE_URL}/orders/{order['id']}/status?new_status=drafted")
        assert resp.status_code == 409

    def test_status_transition_unknown_status(self, order):
        resp = requests.patch(f"{BASE_URL}/orders/{order['id']}/status?new_status=invalid")
        assert resp.status_code == 409
