# repos/supplier_product_rel.py
# This module serves as realtionship layer n2n between Suppliers and Products

from database import SessionLocal
from db_models import Product as DBProduct
from db_models import Supplier as DBSupplier
from db_models import SupplierProduct as DBSupplierProduct
from models import Product, Supplier, SupplierProduct


# check existance of relation
def check_exist(supplier_id: int, product_sku: str) -> bool:
    with SessionLocal() as session:
        return session.query(
            session.query(DBSupplierProduct)
            .filter(
                DBSupplierProduct.supplier_id == supplier_id,
                DBSupplierProduct.sku == product_sku,
            )
            .exists()
        ).scalar()


# create a new relation
def create_rel(supplier_id: int, product_sku: str) -> SupplierProduct:
    with SessionLocal() as session:
        db_rel = DBSupplierProduct(
            sku=product_sku,
            supplier_id=supplier_id,
        )
        session.add(db_rel)
        session.commit()
        session.refresh(db_rel)
        return SupplierProduct.model_validate(db_rel, from_attributes=True)


# get all suppliers for a given sku
def get_rel_by_sku(sku: str) -> list[Supplier]:
    with SessionLocal() as session:
        return [
            Supplier.model_validate(db_supplier, from_attributes=True)
            for db_supplier in session.query(DBSupplier)
            .join(DBSupplierProduct)
            .filter(DBSupplierProduct.sku == sku)
            .all()
        ]


# get all products for a given supplier
def get_rel_by_supplier_id(supplier_id: int) -> list[Product]:
    with SessionLocal() as session:
        return [
            Product.model_validate(db_product, from_attributes=True)
            for db_product in session.query(DBProduct)
            .join(DBSupplierProduct)
            .filter(DBSupplierProduct.supplier_id == supplier_id)
            .all()
        ]


# delete a relation
def delete_rel(supplier_id: int, product_sku: str) -> None:
    with SessionLocal() as session:
        session.query(DBSupplierProduct).filter(
            DBSupplierProduct.supplier_id == supplier_id,
            DBSupplierProduct.sku == product_sku,
        ).delete()
        session.commit()
        return None
