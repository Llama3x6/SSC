# routers/products.py
# This module defines the API endpoints for managing products in the inventory.

from typing import List

from fastapi import APIRouter, HTTPException

import services.products as product_service
from exceptions import (
    DependencyConflictError,
    DuplicateResourceError,
    MismatchedDataError,
    NotFoundError,
)
from models import Product

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[Product])
def list_products():
    """Return all products."""
    return product_service.get_all()


@router.get("/{sku}", response_model=Product)
def get_product(sku: str):
    """Return a single product by its SKU."""
    try:
        product = product_service.get_by_sku(sku)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return product


@router.post("/", response_model=Product, status_code=201)
def create_product(product: Product):
    """Add a new product to the inventory."""
    try:
        created_product = product_service.create_product(product)
    except DuplicateResourceError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return created_product


@router.put("/{sku}", response_model=Product)
def update_product(sku: str, updated_product: Product):
    """Fully replace an existing product."""
    try:
        updated = product_service.update(sku, updated_product)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MismatchedDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return updated


@router.delete("/{sku}", status_code=204)
def delete_product(sku: str):
    """Remove a product from inventory."""
    try:
        product_service.delete(sku)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DependencyConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
