# repos/suppliers.py
# This module serves as the repository layer for managing suppliers in memory.
# cn: Left the previous version of the functions as comments for now, so we can compare the in-memory implementation to the new SQLAlchemy-based implementation.


from database import SessionLocal
from db_models import Supplier as DBSupplier
from models import Supplier

"""
suppliers_db: dict[int, Supplier] = {}
next_supplier_id = 1

# This layer is responsible for direct data access and manipulation,
# such as storing suppliers in memory,
# while the service layer implements business logic and rules.
# This separation allows for cleaner code and easier maintenance.


# ================================================================================
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
"""
# ================================================================================
#


# def check_exist(supplier_id: int) -> bool:
#    """Check if a supplier with the given ID exists."""
#    return supplier_id in suppliers_db


# check_exist with sqlalchemy
def check_exist(supplier_id: int) -> bool:
    with SessionLocal() as session:
        return session.query(
            session.query(DBSupplier).filter(DBSupplier.id == supplier_id).exists()
        ).scalar()


# should we check for duplicate names? maybe not since we can have multiple suppliers with the same name but different IDs, and the ID is the primary key for our operations. If we wanted to enforce unique names, that would be a business rule to implement in the service layer, not the repository layer.
# def get_all() -> list:
#    """Return all suppliers."""
#    return list(suppliers_db.values())


# get_all with sqlalchemy
def get_all() -> list:
    with SessionLocal() as session:
        suppliers = session.query(DBSupplier).all()  # returns list of db types
        return [Supplier.model_validate(s, from_attributes=True) for s in suppliers]


# def get_by_id(supplier_id: int) -> Supplier:
#    """Returns the supplier if found, otherwise returns None."""
#    return suppliers_db.get(supplier_id)


# get_by_id with sqlalchemy
def get_by_id(supplier_id: int) -> Supplier:
    with SessionLocal() as session:
        supplier = (
            session.query(DBSupplier).filter(DBSupplier.id == supplier_id).first()
        )  # returns a type from db
        return Supplier.model_validate(supplier, from_attributes=True)


# def create(supplier: Supplier) -> Supplier:
#    """Add a new supplier and return it."""
#    global next_supplier_id
#    supplier.id = next_supplier_id
#    suppliers_db[next_supplier_id] = supplier
#    next_supplier_id += 1
#    return supplier


# create with sqlalchemy
def create(supplier: Supplier) -> Supplier:
    with SessionLocal() as session:
        db_supplier = DBSupplier(
            name=supplier.name,
            reliability_score=supplier.reliability_score,
            contract_valid_until=supplier.contract_valid_until,
        )
        session.add(db_supplier)
        session.commit()
        session.refresh(db_supplier)  # to get the generated ID
        return Supplier.model_validate(db_supplier, from_attributes=True)


# def update(supplier_id: int, updated_supplier: Supplier) -> Supplier:
#    updated_supplier.id = supplier_id
#    suppliers_db[supplier_id] = updated_supplier
#    return updated_supplier


# update with sqlalchemy
def update(supplier_id: int, updated_supplier: Supplier) -> Supplier:
    with SessionLocal() as session:
        db_supplier = (
            session.query(DBSupplier).filter(DBSupplier.id == supplier_id).first()
        )
        db_supplier.name = updated_supplier.name
        db_supplier.reliability_score = updated_supplier.reliability_score
        db_supplier.contract_valid_until = updated_supplier.contract_valid_until
        session.commit()
        session.refresh(db_supplier)
        return Supplier.model_validate(db_supplier, from_attributes=True)


# def delete(supplier_id: int) -> Supplier:
#    """Remove a supplier and return the deleted supplier."""
#    # cn: This will raise a KeyError if the supplier_id does not exist, which is fine since the service layer should handle that case
#    supplier = suppliers_db.get(supplier_id)
#    del suppliers_db[supplier_id]
#    return supplier


# delete with sqlalchemy
def delete(supplier_id: int) -> Supplier:
    with SessionLocal() as session:
        db_supplier = (
            session.query(DBSupplier).filter(DBSupplier.id == supplier_id).first()
        )
        supplier = Supplier.model_validate(db_supplier, from_attributes=True)
        session.delete(db_supplier)
        session.commit()
        return supplier
