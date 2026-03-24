# repos/suppliers.py
# This module serves as the repository layer for managing suppliers in memory.

# This layer is responsible for direct data access and manipulation,
# such as storing suppliers in memory,
# while the service layer implements business logic and rules.
# This separation allows for cleaner code and easier maintenance.

from database import SessionLocal
from db_models import Supplier as DBSupplier
from models import Supplier


# check_exist with sqlalchemy
def check_exist(supplier_id: int) -> bool:
    with SessionLocal() as session:
        return session.query(
            session.query(DBSupplier).filter(DBSupplier.id == supplier_id).exists()
        ).scalar()


# get_all with sqlalchemy
def get_all() -> list:
    with SessionLocal() as session:
        suppliers = session.query(DBSupplier).all()  # returns list of db types
        return [Supplier.model_validate(s, from_attributes=True) for s in suppliers]


# get_by_id with sqlalchemy
def get_by_id(supplier_id: int) -> Supplier:
    with SessionLocal() as session:
        supplier = (
            session.query(DBSupplier).filter(DBSupplier.id == supplier_id).first()
        )  # returns a type from db
        return Supplier.model_validate(supplier, from_attributes=True)


# create with sqlalchemy
def create(supplier: Supplier) -> Supplier:
    with SessionLocal() as session:
        db_supplier = DBSupplier(
            name=supplier.name,
            country=supplier.country,
            reliability_score=supplier.reliability_score,
            contract_valid_until=supplier.contract_valid_until,
        )
        session.add(db_supplier)
        session.commit()
        session.refresh(db_supplier)  # to get the generated ID
        return Supplier.model_validate(db_supplier, from_attributes=True)


# update with sqlalchemy
def update(supplier_id: int, updated_supplier: Supplier) -> Supplier:
    with SessionLocal() as session:
        db_supplier = (
            session.query(DBSupplier).filter(DBSupplier.id == supplier_id).first()
        )
        db_supplier.name = updated_supplier.name
        db_supplier.country = updated_supplier.country
        db_supplier.reliability_score = updated_supplier.reliability_score
        db_supplier.contract_valid_until = updated_supplier.contract_valid_until
        session.commit()
        session.refresh(db_supplier)
        return Supplier.model_validate(db_supplier, from_attributes=True)


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
