# routers/orders.py
# This module defines the API endpoints for managing orders in the system.

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException

import services.orders as order_service
from exceptions import (
    InvalidRelationshipError,
    InvalidStateTransitionError,
    MismatchedDataError,
    NotFoundError,
)
from models import Order

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=List[Order])
def list_orders(from_date: Optional[date] = None):
    """Return all orders."""
    return order_service.get_all()


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: int):
    """Return a single order by ID."""
    try:
        order = order_service.get_by_id(order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return order


@router.post("/", response_model=Order, status_code=201)
def create_order(order: Order):
    """Create a new order."""
    try:
        created_order = order_service.create(order)
    except MismatchedDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidRelationshipError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return created_order


@router.put("/{order_id}", response_model=Order)
def update_order(order_id: int, updated_order: Order):
    """Replace an existing order."""
    try:
        updated = order_service.update(order_id, updated_order)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MismatchedDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return updated


@router.patch("/{order_id}/status", response_model=Order)
def patch_order(order_id: int, new_status: str):
    """Update the status of an existing order."""
    try:
        updated = order_service.change_status(order_id, new_status)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return updated


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int):
    """Delete an order."""
    try:
        order_service.delete(order_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None
