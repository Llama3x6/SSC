# services/orders.py
# This service layer implements business logic for orders.

import repos.orders as orders_repo
import repos.products as products_repo
import repos.supplier_product_rel as supplierProduct_repo
from exceptions import (
    InvalidRelationshipError,
    InvalidStateTransitionError,
    MismatchedDataError,
    NotFoundError,
)
from models import Order

# This layer is responsible for implementing business logic and rules,
# such as validating state transitions and ensuring data integrity,
# while the repository layer handles direct data access and manipulation.
# This separation allows for cleaner code and easier maintenance.


def get_all() -> list | None:
    """Return all orders."""
    return orders_repo.get_all()


def get_by_id(order_id: int) -> Order | None:
    """Return a single order by ID, or raise NotFoundError if not found."""
    if orders_repo.check_exist_id(order_id):
        return orders_repo.get_by_id(order_id)
    else:
        raise NotFoundError(f"Order with ID '{order_id}' not found")


def create(order):
    """Add a new order and return it.
    - The 'id' field may be ignored; a new ID is generated.
    - 'product_sku' must reference an existing product.
    - 'status' defaults to 'drafted' if not provided."""
    if order.id is not None:
        if orders_repo.check_exist_id(order.id):
            raise MismatchedDataError(
                f"Order with ID '{order.id}' already exists as: id={orders_repo.get_by_id(order.id)}, name={products_repo.get_by_sku(order.product_sku).name}, sku={order.product_sku}, quantity={order.quantity}, status={order.status}, consider leaving ID empty for auto-assignment"
            )
    if not products_repo.check_exist(order.product_sku):
        raise NotFoundError(
            f"Product with SKU '{order.product_sku}' does not exist, cannot create order"
        )
    if not supplierProduct_repo.check_exist(order.supplier_id, order.product_sku):
        raise InvalidRelationshipError(
            f"SupplierProduct with supplier_id={order.supplier_id} and sku={order.product_sku} not found, cannot create order"
        )

    return orders_repo.create(order)


def update(order_id: int, updated_order: Order) -> Order | None:
    if order_id != updated_order.id:
        raise MismatchedDataError("Order ID in URL and body must match")
    if not orders_repo.check_exist_id(order_id):
        raise NotFoundError(f"Order with ID '{order_id}' not found")
    if not supplierProduct_repo.check_exist(
        updated_order.supplier_id, updated_order.product_sku
    ):
        raise InvalidRelationshipError(
            f"SupplierProduct with supplier_id={updated_order.supplier_id} and sku={updated_order.product_sku} not found, cannot update order"
        )
    return orders_repo.update(order_id, updated_order)


def change_status(order_id: int, new_status: str) -> Order | None:
    """
    Update the status of an order with business rule validation.
    Allowed transitions:
      - drafted    → confirmed, cancelled
      - confirmed  → shipped, cancelled
      - shipped    → (none)
      - cancelled  → (none)
    """

    # Define allowed transitions as a dictionary
    allowed_transitions = {
        "drafted": ["confirmed", "cancelled"],
        "confirmed": ["shipped", "cancelled"],
        "shipped": [],  # No transitions from shipped
        "cancelled": [],  # Terminal state
    }
    if not orders_repo.check_exist_id(order_id):
        raise NotFoundError(f"Order with ID '{order_id}' not found")

    order = orders_repo.get_by_id(order_id)

    current = order.status

    # Check if the new status is allowed from the current status
    if new_status not in allowed_transitions.get(current, []):
        raise InvalidStateTransitionError(
            f"Cannot change status from '{current}' to '{new_status}'"
        )

    order.status = new_status
    return orders_repo.update(order_id, order)


def delete(order_id: int) -> Order:
    if not orders_repo.check_exist_id(order_id):
        raise NotFoundError(f"Order with ID '{order_id}' not found")
    return orders_repo.delete(order_id)
