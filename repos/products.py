from typing import Optional

from models import Product

products_db = {}

# Seed some dummy data so we have something to query
products_db["ABC-123456"] = Product(
    sku="ABC-123456", name="Test Widget", current_stock=100, reorder_threshold=20
)
products_db["XYZ-789012"] = Product(
    sku="XYZ-789012", name="Test Gadget", current_stock=5, reorder_threshold=10
)


def check_exist(sku: str) -> bool:
    """Check if a product with the given SKU exists."""
    return sku in products_db


def get_all() -> list:
    """Return all products."""
    return list(products_db.values())


def get_by_sku(sku: str) -> Product:
    """Returns the product if found, otherwise returns None."""
    return products_db.get(sku)


def create(product: Product) -> Product:
    """Add a new product to the inventory and return it."""
    products_db[product.sku] = product
    return product


def update(sku: str, updated_product: Product) -> Product:
    """Fully replace an existing product and return the updated product."""
    products_db[sku] = updated_product
    return updated_product


def delete(sku: str) -> Product:
    """Remove a product from inventory and return the deleted product, or None if not found."""
    deleted_product = products_db.get(sku)
    del products_db[sku]
    return deleted_product
