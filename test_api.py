"""
test_api.py — Integration test suite for the Sentient Supply Chain ERP.

Uses FastAPI TestClient — no live server required.
Each test is isolated via fixtures defined in conftest.py.
Run with: pytest test_api.py -v
"""

import pytest

BASE = ""  # TestClient handles base URL


# ================================================================================
# Products
# ================================================================================


class TestProducts:
    def test_list_products(self, client):
        resp = client.get("/products/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_product(self, client, product):
        assert product["sku"] == "TST-100001"
        assert product["current_stock"] == 100

    def test_create_duplicate_product(self, client, product):
        resp = client.post(
            "/products/",
            json={
                "sku": "TST-100001",
                "name": "Duplicate",
                "current_stock": 10,
                "reorder_threshold": 5,
            },
        )
        assert resp.status_code == 409

    def test_get_product(self, client, product):
        resp = client.get(f"/products/{product['sku']}")
        assert resp.status_code == 200
        assert resp.json()["sku"] == product["sku"]

    def test_get_nonexistent_product(self, client):
        resp = client.get("/products/XXX-000000")
        assert resp.status_code == 404

    def test_update_product(self, client, product):
        updated = product.copy()
        updated["name"] = "Updated Name"
        updated["current_stock"] = 999
        resp = client.put(f"/products/{product['sku']}", json=updated)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"
        assert resp.json()["current_stock"] == 999

    def test_update_product_sku_mismatch(self, client, product):
        resp = client.put("/products/ZZZ-999999", json=product)
        assert resp.status_code == 400

    def test_delete_product(self, client):
        # Use a separate SKU so fixture teardown doesn't double-delete
        data = {
            "sku": "DEL-000001",
            "name": "To Delete",
            "current_stock": 10,
            "reorder_threshold": 5,
        }
        client.post("/products/", json=data)
        resp = client.delete("/products/DEL-000001")
        assert resp.status_code == 204
        assert client.get("/products/DEL-000001").status_code == 404

    def test_delete_product_blocked_by_order(self, client, product, order):
        """Product referenced by an active order must not be deletable."""
        resp = client.delete(f"/products/{product['sku']}")
        assert resp.status_code == 409


# ================================================================================
# Suppliers
# ================================================================================


class TestSuppliers:
    def test_list_suppliers(self, client):
        resp = client.get("/suppliers/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_supplier(self, client, supplier):
        assert supplier["name"] == "Fixture Supplier"
        assert supplier["reliability_score"] == 0.90

    def test_get_supplier(self, client, supplier):
        resp = client.get(f"/suppliers/{supplier['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == supplier["id"]

    def test_get_nonexistent_supplier(self, client):
        resp = client.get("/suppliers/999999")
        assert resp.status_code == 404

    def test_update_supplier(self, client, supplier):
        updated = supplier.copy()
        updated["name"] = "Updated Supplier"
        updated["reliability_score"] = 0.99
        resp = client.put(f"/suppliers/{supplier['id']}", json=updated)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Supplier"

    def test_update_supplier_id_mismatch(self, client, supplier):
        resp = client.put("/suppliers/999999", json=supplier)
        assert resp.status_code == 400

    def test_delete_supplier(self, client):
        data = {
            "name": "To Delete",
            "reliability_score": 0.5,
            "contract_valid_until": "2027-01-01",
        }
        resp = client.post("/suppliers/", json=data)
        assert resp.status_code == 201
        sid = resp.json()["id"]
        assert client.delete(f"/suppliers/{sid}").status_code == 204
        assert client.get(f"/suppliers/{sid}").status_code == 404

    def test_create_supplier_expired_contract(self, client):
        resp = client.post(
            "/suppliers/",
            json={
                "name": "Expired Co",
                "reliability_score": 0.5,
                "contract_valid_until": "2020-01-01",
            },
        )
        assert resp.status_code == 400


# ================================================================================
# Supplier–Product Relations
# ================================================================================


class TestSupplierProductRel:
    def test_create_relation(self, client, supplier_product, supplier, product):
        assert supplier_product["supplier_id"] == supplier["id"]
        assert supplier_product["sku"] == product["sku"]

    def test_create_duplicate_relation(
        self, client, supplier_product, supplier, product
    ):
        resp = client.post(
            "/supplier-product/",
            json={
                "supplier_id": supplier["id"],
                "sku": product["sku"],
            },
        )
        assert resp.status_code == 409

    def test_get_suppliers_by_sku(self, client, supplier_product, product):
        resp = client.get(f"/supplier-product/by_sku/{product['sku']}")
        assert resp.status_code == 200
        assert any(s["id"] for s in resp.json())

    def test_get_products_by_supplier(self, client, supplier_product, supplier):
        resp = client.get(f"/supplier-product/by_supplier/{supplier['id']}")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_by_nonexistent_sku(self, client):
        resp = client.get("/supplier-product/by_sku/XXX-000000")
        assert resp.status_code == 404

    def test_recommend_suppliers(self, client, supplier_product, product):
        resp = client.get(
            f"/supplier-product/supplier_recommendations?sku={product['sku']}"
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# ================================================================================
# Orders
# ================================================================================


class TestOrders:
    def test_list_orders(self, client):
        resp = client.get("/orders/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_order(self, client, order, product, supplier):
        assert order["product_sku"] == product["sku"]
        assert order["supplier_id"] == supplier["id"]
        assert order["status"] == "drafted"

    def test_create_order_nonexistent_product(self, client, supplier):
        resp = client.post(
            "/orders/",
            json={
                "product_sku": "BAD-000000",
                "supplier_id": supplier["id"],
                "quantity": 5,
                "status": "drafted",
            },
        )
        assert resp.status_code == 404

    def test_create_order_invalid_supplier_product_rel(self, client, product):
        """Supplier exists but does not supply this product — must fail."""
        # Create a second supplier with no relation to the product
        s2 = client.post(
            "/suppliers/",
            json={
                "name": "Unrelated Supplier",
                "reliability_score": 0.6,
                "contract_valid_until": "2027-01-01",
            },
        ).json()
        resp = client.post(
            "/orders/",
            json={
                "product_sku": product["sku"],
                "supplier_id": s2["id"],
                "quantity": 5,
                "status": "drafted",
            },
        )
        assert resp.status_code == 409
        client.delete(f"/suppliers/{s2['id']}")

    def test_get_order(self, client, order):
        resp = client.get(f"/orders/{order['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == order["id"]

    def test_get_nonexistent_order(self, client):
        resp = client.get("/orders/999999")
        assert resp.status_code == 404

    def test_update_order(self, client, order, product, supplier):
        updated = {
            "id": order["id"],
            "product_sku": product["sku"],
            "supplier_id": supplier["id"],
            "quantity": 99,
            "status": "drafted",
            "order_date": "2026-01-01",
        }
        resp = client.put(f"/orders/{order['id']}", json=updated)
        assert resp.status_code == 200
        assert resp.json()["quantity"] == 99

    def test_status_transition_drafted_to_confirmed(self, client, order):
        resp = client.patch(f"/orders/{order['id']}/status?new_status=confirmed")
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"

    def test_status_transition_invalid(self, client, order):
        client.patch(f"/orders/{order['id']}/status?new_status=confirmed")
        client.patch(f"/orders/{order['id']}/status?new_status=shipped")
        resp = client.patch(f"/orders/{order['id']}/status?new_status=drafted")
        assert resp.status_code == 409

    def test_status_transition_unknown_status(self, client, order):
        resp = client.patch(f"/orders/{order['id']}/status?new_status=banana")
        assert resp.status_code == 409

    def test_delete_order(self, client, supplier_product, supplier, product):
        o = client.post(
            "/orders/",
            json={
                "product_sku": product["sku"],
                "supplier_id": supplier["id"],
                "quantity": 1,
                "status": "drafted",
            },
        ).json()
        assert client.delete(f"/orders/{o['id']}").status_code == 204
        assert client.get(f"/orders/{o['id']}").status_code == 404
