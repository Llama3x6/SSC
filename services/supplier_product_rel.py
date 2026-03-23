# services/supplier_product_rel.py
# This module defines the services for the supplier-product relationship.

import repos.supplier_product_rel as supplierProduct_repo
from exceptions import (
    DuplicateResourceError,
    NotFoundError,
)
from models import Product, Supplier, SupplierProduct


def create_rel(supplier_id: int, product_sku: str) -> SupplierProduct:
    if supplierProduct_repo.check_exist(supplier_id, product_sku):
        raise DuplicateResourceError(
            f"SupplierProduct with supplier_id={supplier_id} and sku={product_sku} already exists."
        )
    return supplierProduct_repo.create_rel(supplier_id, product_sku)


def check_exist(supplier_id: int, product_sku: str) -> bool:
    return supplierProduct_repo.check_exist(supplier_id, product_sku)


def get_rel_by_supplier_id(supplier_id: int) -> list[Product]:
    id_rel = supplierProduct_repo.get_rel_by_supplier_id(supplier_id)
    if not id_rel:
        raise NotFoundError(
            f"SupplierProduct with supplier_id={supplier_id} not found."
        )
    return id_rel


def get_rel_by_sku(product_sku: str) -> list[Supplier]:
    sku_rel = supplierProduct_repo.get_rel_by_sku(product_sku)
    if not sku_rel:
        raise NotFoundError(f"SupplierProduct with sku={product_sku} not found.")
    return sku_rel


def delete_rel(supplier_id: int, product_sku: str) -> None:
    if not supplierProduct_repo.check_exist(supplier_id, product_sku):
        raise NotFoundError(
            f"SupplierProduct with supplier_id={supplier_id} and sku={product_sku} not found."
        )
    supplierProduct_repo.delete_rel(supplier_id, product_sku)


# reccomend suppliers based on reliability_score
def recommend_suppliers(product_sku: str) -> list[Supplier]:
    best_suppliers = []
    suppliers = supplierProduct_repo.get_rel_by_sku(product_sku)
    if not suppliers:
        raise NotFoundError(f"SupplierProduct with sku={product_sku} not found.")
    max_score = max(supplier.reliability_score for supplier in suppliers)

    for supplier in suppliers:
        if supplier.reliability_score >= max_score - 0.2:
            best_suppliers.append(supplier)
    best_suppliers.sort(key=lambda s: s.reliability_score, reverse=True)
    return best_suppliers
