# test_models.py

from datetime import date

from pydantic import ValidationError

from models import Order, Product, Supplier

try:
    reliable_supplier = Supplier(
        id=1,
        name="Logistics AG",
        reliability_score=0.95,
        contract_valid_until=date(2026, 1, 31),
    )

    print("✅ Valid Supplier Created:", reliable_supplier)
except ValidationError as e:
    print("❌ Supplier Failed:", e)


# Test 2: Should FAIL (negative stock)
try:
    invalid_product = Product(
        sku="INV-001001",
        name="Invalid Item",
        current_stock=-5,  # Business logic violation!
        reorder_threshold=10,
    )
except ValidationError as e:
    print("✅ Correctly caught invalid product:", e.errors()[0]["msg"])
