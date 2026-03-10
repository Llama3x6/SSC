from datetime import date

from models import Supplier

suppliers_db: dict[int, Supplier] = {}
next_supplier_id = 1

# This layer is responsible for direct data access and manipulation,
# such as storing suppliers in memory,
# while the service layer implements business logic and rules.
# This separation allows for cleaner code and easier maintenance.


# ================================================================================
# Seed some suppliers
#
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

# ================================================================================
#


def check_exist(supplier_id: int) -> bool:
    """Check if a supplier with the given ID exists."""
    return supplier_id in suppliers_db


# should we check for duplicate names? maybe not since we can have multiple suppliers with the same name but different IDs, and the ID is the primary key for our operations. If we wanted to enforce unique names, that would be a business rule to implement in the service layer, not the repository layer.
def get_all() -> list:
    """Return all suppliers."""
    return list(suppliers_db.values())


def get_by_id(supplier_id: int) -> Supplier:
    """Returns the supplier if found, otherwise returns None."""
    return suppliers_db.get(supplier_id)


def create(supplier: Supplier) -> Supplier:
    """Add a new supplier and return it."""
    global next_supplier_id
    supplier.id = next_supplier_id
    suppliers_db[next_supplier_id] = supplier
    next_supplier_id += 1
    return supplier


def update(supplier_id: int, updated_supplier: Supplier) -> Supplier:
    updated_supplier.id = supplier_id
    suppliers_db[supplier_id] = updated_supplier
    return updated_supplier


def delete(supplier_id: int) -> Supplier:
    """Remove a supplier and return the deleted supplier."""
    # cn: This will raise a KeyError if the supplier_id does not exist, which is fine since the service layer should handle that case
    supplier = suppliers_db.get(supplier_id)
    del suppliers_db[supplier_id]
    return supplier
