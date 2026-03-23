# routers/suppliers.py
# This module defines the API endpoints for managing suppliers in the system.

from typing import List

from fastapi import APIRouter, HTTPException

import services.suppliers as supplier_service
from exceptions import (
    ContractTimeError,
    DuplicateResourceError,
    MismatchedDataError,
    NotFoundError,
)
from models import Supplier

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("/", response_model=List[Supplier])
def list_suppliers():
    """Return all suppliers."""
    return supplier_service.get_all()


@router.get("/{supplier_id}", response_model=Supplier)
def get_supplier(supplier_id: int):
    """Return a single supplier by ID."""
    try:
        supplier = supplier_service.get_by_id(supplier_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return supplier


@router.post("/", response_model=Supplier, status_code=201)
def create_supplier(supplier: Supplier):
    """Create a new supplier."""
    try:
        created_supplier = supplier_service.create(supplier)
    except DuplicateResourceError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ContractTimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return created_supplier


@router.put("/{supplier_id}", response_model=Supplier)
def update_supplier(supplier_id: int, updated_supplier: Supplier):
    """Replace an existing supplier."""
    try:
        updated = supplier_service.update(supplier_id, updated_supplier)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MismatchedDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ContractTimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return updated


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(supplier_id: int):
    """Delete a supplier."""
    try:
        supplier_service.delete(supplier_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
