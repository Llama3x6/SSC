from models import Order

# This layer is responsible for direct data access and manipulation,
# such as storing orders in memory,
# while the service layer implements business logic and rules.
# This separation allows for cleaner code and easier maintenance.


orders_db: dict[int, Order] = {}
next_order_id = 1

# Seed a few orders (assuming products ABC-123456 and XYZ-789012 exist)
orders_db[1] = Order(id=1, product_sku="ABC-123456", quantity=10, status="drafted")
orders_db[2] = Order(id=2, product_sku="XYZ-789012", quantity=5, status="confirmed")
next_order_id = 3


def check_exist_id(order_id: int) -> bool:
    """Check if an order exists by ID."""
    return order_id in orders_db


def check_exist_sku(sku: str) -> bool:
    """Check if an order exists by product SKU."""
    return any(order.product_sku == sku for order in orders_db.values())


def get_all() -> list:
    """Return all orders."""
    return list(orders_db.values())


def get_by_id(order_id: int) -> Order:
    return orders_db.get(order_id)


def create(order: Order) -> Order:
    """Add a new order and return it. Manage id assignment here."""
    global next_order_id
    order.id = next_order_id
    orders_db[next_order_id] = order
    next_order_id += 1
    return order


def update(order_id: int, updated_order: Order) -> Order:
    updated_order.id = order_id
    orders_db[order_id] = updated_order
    return updated_order


def delete(order_id: int) -> Order:
    deleted_order = orders_db.get(order_id)
    del orders_db[order_id]
    return deleted_order
