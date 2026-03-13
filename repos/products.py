# repos/products.py
# This module serves as the repository layer for managing products in memory.
# cn: Left the previous version of the functions as comments for now, so we can compare the in-memory implementation to the new SQLAlchemy-based implementation.

from database import SessionLocal
from db_models import Product as DBProduct
from models import Product

"""
products_db = {}

# Seed some dummy data so we have something to query
products_db["ABC-123456"] = Product(
    sku="ABC-123456", name="Test Widget", current_stock=100, reorder_threshold=20
)
products_db["XYZ-789012"] = Product(
    sku="XYZ-789012", name="Test Gadget", current_stock=5, reorder_threshold=10
)
"""


# def check_exist(sku: str) -> bool:
#    """Check if a product with the given SKU exists."""
#    return sku in products_db


# check_exist with sqlalchemy
def check_exist(sku: str) -> bool:
    with SessionLocal() as session:
        return session.query(
            session.query(DBProduct).filter(DBProduct.sku == sku).exists()
        ).scalar()


# def get_all() -> list:
#    """Return all products."""
#    return list(products_db.values())


# get_all with sqlalchemy
def get_all() -> list:
    with SessionLocal() as session:
        products = session.query(DBProduct).all()  # returns list of db types
        return [Product.model_validate(p, from_attributes=True) for p in products]


# def get_by_sku(sku: str) -> Product:
#    """Returns the product if found, otherwise returns None."""
#    return products_db.get(sku)


# get_by_sku with sqlalchemy
def get_by_sku(sku: str) -> Product:
    with SessionLocal() as session:
        product = (
            session.query(DBProduct).filter(DBProduct.sku == sku).first()
        )  # returns a type from db
        return Product.model_validate(product, from_attributes=True)


# def create(product: Product) -> Product:
#    """Add a new product to the inventory and return it."""
#    products_db[product.sku] = product
#    return product


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


# def update(sku: str, updated_product: Product) -> Product:
#    """Fully replace an existing product and return the updated product."""
#    products_db[sku] = updated_product
#    return updated_product


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


# def delete(sku: str) -> Product:
#    """Remove a product from inventory and return the deleted product, or None if not found."""
#    deleted_product = products_db.get(sku)
#    del products_db[sku]
#    return deleted_product


# delete with sqlalchemy
def delete(sku: str) -> Product:
    with SessionLocal() as session:
        db_product = session.query(DBProduct).filter(DBProduct.sku == sku).first()
        deleted_product = Product.model_validate(db_product, from_attributes=True)
        session.delete(db_product)
        session.commit()
        return deleted_product
