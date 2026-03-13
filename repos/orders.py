# repos/orders.py
# This module serves as the repository layer for managing orders in memory.
# # cn: Left the previous version of the functions as comments for now, so we can compare the in-memory implementation to the new SQLAlchemy-based implementation.


from database import SessionLocal
from db_models import Order as DBOrder
from db_models import Product as DBProduct
from models import Order

"""
orders_db: dict[int, Order] = {}
next_order_id = 1

# Seed a few orders (assuming products ABC-123456 and XYZ-789012 exist)
orders_db[1] = Order(id=1, product_sku="ABC-123456", quantity=10, status="drafted")
orders_db[2] = Order(id=2, product_sku="XYZ-789012", quantity=5, status="confirmed")
next_order_id = 3
"""


# def check_exist_id(order_id: int) -> bool:
#    """Check if an order exists by ID."""
#    return order_id in orders_db


# check_exist_id with sqlalchemy
def check_exist_id(order_id: int) -> bool:
    with SessionLocal() as session:
        return session.query(
            session.query(DBOrder).filter(DBOrder.id == order_id).exists()
        ).scalar()


# def check_exist_sku(sku: str) -> bool:
#    """Check if an order exists by product SKU."""
#    return any(order.product_sku == sku for order in orders_db.values())


# check_exist_sku with sqlalchemy
def check_exist_sku(sku: str) -> bool:
    with SessionLocal() as session:
        return session.query(
            session.query(DBOrder).filter(DBOrder.product_sku == sku).exists()
        ).scalar()


# def get_all() -> list:
#    """Return all orders."""
#    return list(orders_db.values())


# get_all with sqlalchemy
def get_all() -> list:
    with SessionLocal() as session:
        orders = session.query(DBOrder).all()  # returns list of db types
        return [Order.model_validate(o, from_attributes=True) for o in orders]


# def get_by_id(order_id: int) -> Order:
#    return orders_db.get(order_id)


# get_by_id with sqlalchemy
def get_by_id(order_id: int) -> Order:
    with SessionLocal() as session:
        order = (
            session.query(DBOrder).filter(DBOrder.id == order_id).first()
        )  # returns a type from db
        return Order.model_validate(order, from_attributes=True)


# def create(order: Order) -> Order:
#    """Add a new order and return it. Manage id assignment here."""
#    global next_order_id
#    order.id = next_order_id
#    orders_db[next_order_id] = order
#    next_order_id += 1
#    return order


# create with sqlalchemy
def create(order: Order) -> Order:
    with SessionLocal() as session:
        db_order = DBOrder(
            # product_id=order.product_id, # we need to set this for the foreign key constraint, but it won't be in the Order model since it's not exposed via the API
            product_id=session.query(DBProduct.id)
            .filter(DBProduct.sku == order.product_sku)
            .scalar(),  # look up the product ID based on the SKU
            product_sku=order.product_sku,
            quantity=order.quantity,
            order_date=order.order_date,
            status=order.status,
        )
        session.add(db_order)
        session.commit()
        session.refresh(db_order)  # to get the generated ID
        return Order.model_validate(db_order, from_attributes=True)


# def update(order_id: int, updated_order: Order) -> Order:
#    updated_order.id = order_id
#    orders_db[order_id] = updated_order
#    return updated_order


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
        db_order.quantity = updated_order.quantity
        db_order.order_date = updated_order.order_date
        db_order.status = updated_order.status
        session.commit()
        session.refresh(db_order)
        return Order.model_validate(db_order, from_attributes=True)


# def delete(order_id: int) -> Order:
#    deleted_order = orders_db.get(order_id)
#    del orders_db[order_id]
#    return deleted_order


# delete with sqlalchemy
def delete(order_id: int) -> Order:
    with SessionLocal() as session:
        db_order = session.query(DBOrder).filter(DBOrder.id == order_id).first()
        order = Order.model_validate(db_order, from_attributes=True)
        session.delete(db_order)
        session.commit()
        return order
