from datetime import datetime

import repos.products as product_repo
import repos.suppliers as supplier_repo
from exceptions import (
    ContractTimeError,
    DependencyConflictError,
    DuplicateResourceError,
    MismatchedDataError,
    NotFoundError,
)
from models import Supplier


def get_all() -> list:
    """Return all suppliers."""
    return supplier_repo.get_all()


def get_by_id(supplier_id: int) -> Supplier:
    if supplier_repo.check_exist(supplier_id):
        return supplier_repo.get_by_id(supplier_id)
    else:
        raise NotFoundError(f"Supplier with ID '{supplier_id}' not found")


def create(supplier: Supplier) -> Supplier:
    """Add a new supplier and return it."""
    if supplier.id is not None:
        if supplier_repo.check_exist(supplier.id):
            raise DuplicateResourceError(
                f"Supplier with ID '{supplier.id}' already exists"
            )
    if supplier.contract_valid_until < datetime.now().date():
        raise ContractTimeError("Contract valid until date must be in the future")
    return supplier_repo.create(supplier)


def update(supplier_id: int, updated_supplier: Supplier) -> Supplier:
    if supplier_id != updated_supplier.id:
        raise MismatchedDataError("Supplier ID in URL and body must match")
    if not supplier_repo.check_exist(supplier_id):
        raise NotFoundError(f"Supplier with ID '{supplier_id}' not found")
    if updated_supplier.contract_valid_until < datetime.now().date():
        raise ContractTimeError("Contract valid until date must be in the future")
    else:
        return supplier_repo.update(supplier_id, updated_supplier)


def delete(supplier_id: int) -> Supplier:
    if not supplier_repo.check_exist(supplier_id):
        raise NotFoundError(f"Supplier with ID '{supplier_id}' not found")
    # Check if any products reference this supplier ID before deletion
    #    for product in product_repo.get_all():
    #        if product.supplier_id == supplier_id:
    #           do some type of logging here to indicate that we have a product that references this supplier, but since we don't have a requirement to prevent deletion of suppliers that are referenced by products, we will allow the deletion to proceed. In a real application, we might want to implement a soft delete or mark the supplier as inactive instead of hard deleting it, to preserve referential integrity and historical data.
    return supplier_repo.delete(supplier_id)
