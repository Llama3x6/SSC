# repos/products.py
# This module serves as the repository layer for managing products in memory.

from database import SessionLocal
from db_models import Product as DBProduct
from models import Product


# check_exist with sqlalchemy
def check_exist(sku: str) -> bool:
    with SessionLocal() as session:
        return session.query(
            session.query(DBProduct).filter(DBProduct.sku == sku).exists()
        ).scalar()


# get_all with sqlalchemy
def get_all() -> list:
    with SessionLocal() as session:
        products = session.query(DBProduct).all()  # returns list of db types
        return [Product.model_validate(p, from_attributes=True) for p in products]


# get_by_sku with sqlalchemy
def get_by_sku(sku: str) -> Product:
    with SessionLocal() as session:
        product = (
            session.query(DBProduct).filter(DBProduct.sku == sku).first()
        )  # returns a type from db
        return Product.model_validate(product, from_attributes=True)


# create with sqlalchemy
def create(product: Product) -> Product:
    with SessionLocal() as session:
        db_product = DBProduct(
            sku=product.sku,
            name=product.name,
            current_stock=product.current_stock,
            reorder_threshold=product.reorder_threshold,
        )
        session.add(db_product)
        session.commit()
        session.refresh(db_product)
        return Product.model_validate(db_product, from_attributes=True)


# update with sqlalchemy
def update(sku: str, updated_product: Product) -> Product:
    with SessionLocal() as session:
        db_product = session.query(DBProduct).filter(DBProduct.sku == sku).first()
        db_product.name = updated_product.name
        db_product.current_stock = updated_product.current_stock
        db_product.reorder_threshold = updated_product.reorder_threshold
        session.commit()
        session.refresh(db_product)
        return Product.model_validate(db_product, from_attributes=True)


# delete with sqlalchemy
def delete(sku: str) -> Product:
    with SessionLocal() as session:
        db_product = session.query(DBProduct).filter(DBProduct.sku == sku).first()
        deleted_product = Product.model_validate(db_product, from_attributes=True)
        session.delete(db_product)
        session.commit()
        return deleted_product
