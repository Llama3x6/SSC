import json

import requests

BASE_URL = "http://127.0.0.1:8000"

# Summary counters
passed = 0
failed = 0
failures = []


def print_response(resp, expected_status):
    global passed, failed, failures
    status = resp.status_code
    print(f"Status: {status} (expected {expected_status})")
    if status != expected_status:
        failed += 1
        failures.append(f"Expected {expected_status}, got {status} - {resp.url}")
        print(f"  ERROR: {resp.text}")
    else:
        passed += 1
        try:
            print(f"  Data: {json.dumps(resp.json(), indent=2)}")
        except:
            print(f"  (No JSON content)")
    print("-" * 40)


# ================================================================#
# ================================================================#
# --- Products ---
#
print("=== PRODUCT TESTS ===")

# List products (initially seeded)
resp = requests.get(f"{BASE_URL}/products")
print_response(resp, 200)

# Create a new product that will be deleted later
new_product = {
    "sku": "TST-123456",
    "name": "Test Product",
    "current_stock": 100,
    "reorder_threshold": 20,
}
# Recreate the seeded product from in-memory repo to ensure it exists for the tests. This is necessary because we switched to a real database and the in-memory seeding no longer applies. In a real test suite, we would have proper setup/teardown to handle this.
new_product_seed = {
    "sku": "ABC-123456",
    "name": "Test Widget",
    "current_stock": 100,
    "reorder_threshold": 20,
}


resp = requests.post(f"{BASE_URL}/products", json=new_product)
print_response(resp, 201)

resp_seed = requests.post(f"{BASE_URL}/products", json=new_product_seed)
print_response(resp_seed, 201)

# Try to create duplicate SKU
resp = requests.post(f"{BASE_URL}/products", json=new_product)
print_response(resp, 409)  # Should be duplicate error

# Get the new product
resp = requests.get(f"{BASE_URL}/products/TST-123456")
print_response(resp, 200)

# Update the product
updated_product = new_product.copy()
updated_product["name"] = "Updated Test Product"
updated_product["current_stock"] = 150
resp = requests.put(f"{BASE_URL}/products/TST-123456", json=updated_product)
print_response(resp, 200)

# Get again to verify update
resp = requests.get(f"{BASE_URL}/products/TST-123456")
print_response(resp, 200)


# --------DEBUGGED but weird doublecheck--------
# Try to update non-existent SKU
resp = requests.put(
    f"{BASE_URL}/products/NO-SKU", json=updated_product
)  # updated_product has a SKU of TST-123456, but URL is NO-SKU, so this should trigger the MismatchedDataError
print_response(resp, 400)

# Delete the product
resp = requests.delete(f"{BASE_URL}/products/TST-123456")
print_response(resp, 204)

# Verify deletion
resp = requests.get(f"{BASE_URL}/products/TST-123456")
print_response(resp, 404)

# --- Test product deletion guard (product with existing orders) ---
print("\n--- Testing product deletion guard ---")
# Create a product specifically for this test
guard_product = {
    "sku": "GRD-987654",
    "name": "Guard Test Product",
    "current_stock": 10,
    "reorder_threshold": 5,
}
resp = requests.post(f"{BASE_URL}/products", json=guard_product)
print_response(resp, 201)
guard_sku = guard_product["sku"]

# Create an order referencing this product
guard_order = {"product_sku": guard_sku, "quantity": 2, "status": "drafted"}
resp = requests.post(f"{BASE_URL}/orders", json=guard_order)
print_response(resp, 201)
guard_order_id = resp.json()["id"]

# Attempt to delete the product (should fail with 409)
resp = requests.delete(f"{BASE_URL}/products/{guard_sku}")
print_response(resp, 409)

# Clean up: delete the order first
resp = requests.delete(f"{BASE_URL}/orders/{guard_order_id}")
print_response(resp, 204)

# Now delete the product (should succeed)
resp = requests.delete(f"{BASE_URL}/products/{guard_sku}")
print_response(resp, 204)

print("--- Product deletion guard test complete ---\n")


# ================================================================#
# ================================================================#
# --- Suppliers ---
#
print("\n=== SUPPLIER TESTS ===")

# List suppliers (seeded)
resp = requests.get(f"{BASE_URL}/suppliers")
print_response(resp, 200)

# Create a new supplier
new_supplier = {
    "name": "Test Supplier",
    "reliability_score": 0.85,
    "contract_valid_until": "2026-12-31",
}
resp = requests.post(f"{BASE_URL}/suppliers", json=new_supplier)
print_response(resp, 201)
supplier_id = resp.json()["id"]

# ------------------------------------------
# Try duplicate name (should fail)
# #cn: Since we decided that duplicate names are allowed, this test is not valid. If we wanted to enforce unique names, we would implement that logic in the service layer and then this test would be relevant. For now, we will skip this test since our current business rules do not prohibit duplicate supplier names.
# dup_supplier = new_supplier.copy()
# dup_supplier["name"] = "Test Supplier"  # same name
# resp = requests.post(f"{BASE_URL}/suppliers", json=dup_supplier)
# print_response(resp, 400)
# ------------------------------------------

# Get the supplier
resp = requests.get(f"{BASE_URL}/suppliers/{supplier_id}")
print_response(resp, 200)

# Update supplier
updated_supplier = {
    "id": supplier_id,
    "name": "Updated Test Supplier",
    "reliability_score": 0.9,
    "contract_valid_until": "2027-01-01",
}
resp = requests.put(f"{BASE_URL}/suppliers/{supplier_id}", json=updated_supplier)
print_response(resp, 200)

# Delete supplier
resp = requests.delete(f"{BASE_URL}/suppliers/{supplier_id}")
print_response(resp, 204)


# ================================================================#
# ================================================================#
# --- Orders ---
#
print("\n=== ORDER TESTS ===")

# We need a product to reference. Use the seeded ABC-123456.
product_sku = "ABC-123456"

# List orders (seeded)
resp = requests.get(f"{BASE_URL}/orders")
print_response(resp, 200)

# Create a new order
new_order = {"product_sku": product_sku, "quantity": 5, "status": "drafted"}
resp = requests.post(f"{BASE_URL}/orders", json=new_order)
print_response(resp, 201)
order_id = resp.json()["id"]

# --------DEBUGGed--------
# test wanted 400 but passes a sku that is a valid str so the correct error is 404 not found, since the service layer checks if the SKU exists in the products repo and raises a NotFoundError if it doesn't
# Try to create order with non-existent SKU
bad_order = {"product_sku": "BAD-SKU", "quantity": 5, "status": "drafted"}
resp = requests.post(f"{BASE_URL}/orders", json=bad_order)
print_response(resp, 404)

# Get the order
resp = requests.get(f"{BASE_URL}/orders/{order_id}")
print_response(resp, 200)

# Update order
updated_order = {
    "id": order_id,
    "product_sku": product_sku,
    "quantity": 10,
    "status": "confirmed",
    "order_date": "2026-02-16",
}
resp = requests.put(f"{BASE_URL}/orders/{order_id}", json=updated_order)
print_response(resp, 200)

# Change status via PATCH
resp = requests.patch(f"{BASE_URL}/orders/{order_id}/status?new_status=shipped")
print_response(resp, 200)

# Try invalid status
resp = requests.patch(f"{BASE_URL}/orders/{order_id}/status?new_status=invalid")
print_response(resp, 409)

# Delete order
resp = requests.delete(f"{BASE_URL}/orders/{order_id}")
print_response(resp, 204)


# ================================================================#
# ================================================================#
# --- Summary ---
#
print("\n" + "=" * 40)
print(f"TESTS COMPLETE: {passed} passed, {failed} failed")
if failed > 0:
    print("\nFAILURES:")
    for f in failures:
        print(f"  - {f}")
else:
    print("✅ ALL TESTS PASSED")
print("=" * 40)
