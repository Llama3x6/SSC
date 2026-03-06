from datetime import date
from typing import Optional

from models import Supplier

suppliers_db = {}
next_supplier_id = 1

# Seed some suppliers
suppliers_db[1] = Supplier(
    id=1,
    name="LogiCo AG",
    reliability_score=0.95,
    contract_valid_until=date(2025, 12, 31),
)
suppliers_db[2] = Supplier(
    id=2,
    name="Parts GmbH",
    reliability_score=0.82,
    contract_valid_until=date(2024, 6, 30),
)
next_supplier_id = 3


def get_all() -> list:
    """Return all suppliers."""
    return list(suppliers_db.values())


def get_by_id(supplier_id: int) -> Optional[Supplier]:
    """Returns the supplier if found, otherwise returns None."""
    return suppliers_db.get(supplier_id)


def create(supplier: Supplier) -> Supplier:
    """Add a new supplier and return it."""
    global next_supplier_id
    supplier.id = next_supplier_id
    suppliers_db[next_supplier_id] = supplier
    next_supplier_id += 1
    return supplier


def update(supplier_id: int, updated_supplier: Supplier) -> Optional[Supplier]:
    """Fully replace an existing supplier and return the updated supplier, or None if not found."""
    if supplier_id not in suppliers_db:
        return None
    updated_supplier.id = supplier_id
    suppliers_db[supplier_id] = updated_supplier
    return updated_supplier


def delete(supplier_id: int) -> Optional[Supplier]:
    """Remove a supplier and return the deleted supplier, or None if not found."""
    deleted_supplier = suppliers_db.get(supplier_id)
    if deleted_supplier is None:
        return None
    else:
        del suppliers_db[supplier_id]
        return deleted_supplier
