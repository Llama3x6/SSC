# repos/orders.py
# This module serves as the repository layer for managing orders.


from database import SessionLocal
from db_models import Order as DBOrder
from db_models import Product as DBProduct
from models import Order


# check_exist_id with sqlalchemy
def check_exist_id(order_id: int) -> bool:
    with SessionLocal() as session:
        return session.query(
            session.query(DBOrder).filter(DBOrder.id == order_id).exists()
        ).scalar()


# check_exist_sku with sqlalchemy
def check_exist_sku(sku: str) -> bool:
    with SessionLocal() as session:
        return session.query(
            session.query(DBOrder).filter(DBOrder.product_sku == sku).exists()
        ).scalar()


# get_all with sqlalchemy
def get_all(from_date=None) -> list:
    with SessionLocal() as session:
        query = session.query(DBOrder)
        if from_date:
            query = query.filter(DBOrder.order_date >= from_date)
        orders = query.all()
        return [Order.model_validate(o, from_attributes=True) for o in orders]


# get_by_id with sqlalchemy
def get_by_id(order_id: int) -> Order:
    with SessionLocal() as session:
        order = (
            session.query(DBOrder).filter(DBOrder.id == order_id).first()
        )  # returns a type from db
        return Order.model_validate(order, from_attributes=True)


# create with sqlalchemy
def create(order: Order) -> Order:
    with SessionLocal() as session:
        db_order = DBOrder(
            # product_id=order.product_id, # we need to set this for the foreign key constraint, but it won't be in the Order model since it's not exposed via the API
            product_id=session.query(DBProduct.id)
            .filter(DBProduct.sku == order.product_sku)
            .scalar(),  # look up the product ID based on the SKU
            product_sku=order.product_sku,
            supplier_id=order.supplier_id,
            quantity=order.quantity,
            order_date=order.order_date,
            status=order.status,
        )
        session.add(db_order)
        session.commit()
        session.refresh(db_order)  # to get the generated ID
        return Order.model_validate(db_order, from_attributes=True)


# update with sqlalchemy
def update(order_id: int, updated_order: Order) -> Order:
    with SessionLocal() as session:
        db_order = session.query(DBOrder).filter(DBOrder.id == order_id).first()
        db_order.product_id = (
            session.query(DBProduct.id)
            .filter(DBProduct.sku == updated_order.product_sku)
            .scalar()
        )  # look up the product ID based on the SKU
        db_order.product_sku = updated_order.product_sku
        db_order.supplier_id = updated_order.supplier_id
        db_order.quantity = updated_order.quantity
        db_order.order_date = updated_order.order_date
        db_order.status = updated_order.status
        session.commit()
        session.refresh(db_order)
        return Order.model_validate(db_order, from_attributes=True)


# delete with sqlalchemy
def delete(order_id: int) -> Order:
    with SessionLocal() as session:
        db_order = session.query(DBOrder).filter(DBOrder.id == order_id).first()
        order = Order.model_validate(db_order, from_attributes=True)
        session.delete(db_order)
        session.commit()
        return order
