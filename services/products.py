# services/products.py
# This service layer implements business logic for products.

import repos.orders as orders_repo
import repos.products as product_repo
from exceptions import (
    DependencyConflictError,
    DuplicateResourceError,
    MismatchedDataError,
    NotFoundError,
)
from models import Product


def get_all() -> list:
    """Return all products in inventory."""
    return product_repo.get_all()


def get_by_sku(sku: str) -> Product:
    if product_repo.check_exist(sku):
        return product_repo.get_by_sku(sku)
    else:
        raise NotFoundError(f"Product with SKU '{sku}' not found")


def create_product(product: Product) -> Product:
    if product_repo.check_exist(product.sku):
        raise DuplicateResourceError(
            f"Product with SKU '{product.sku}' already exists as: sku={product.sku}, name={product.name}, current_stock={product.current_stock}, reorder_threshold={product.reorder_threshold}"
        )
    return product_repo.create(product)


def update(sku: str, updated_product: Product) -> Product:
    if sku != updated_product.sku:
        raise MismatchedDataError("Product SKU in URL and body must match")
    if not product_repo.check_exist(sku):
        raise NotFoundError(f"Product with SKU '{sku}' not found")
    else:
        return product_repo.update(sku, updated_product)


def delete(sku: str) -> Product:
    if not product_repo.check_exist(sku):
        raise NotFoundError(f"Product with SKU '{sku}' not found")
    # Check if any orders reference this product SKU before deletion
    for order in orders_repo.get_all():
        if order.product_sku == sku:
            raise DependencyConflictError(
                f"Cannot delete product with SKU '{sku}' because it is referenced by existing orders as: id={order.id}, product_sku={order.product_sku}, quantity={order.quantity}, status={order.status}"
            )
    return product_repo.delete(sku)
