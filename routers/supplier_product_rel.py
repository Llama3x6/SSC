# routers/supplier_product_rel.py
# This module defines the routes for the supplier-product relationship.


from typing import List

from fastapi import APIRouter, HTTPException

import services.supplier_product_rel as supplierProduct_service
from exceptions import (
    DuplicateResourceError,
    NotFoundError,
)
from models import Product, Supplier, SupplierProduct

router = APIRouter(prefix="/supplier-product", tags=["supplier-product"])


@router.get("/by_sku/{sku}", response_model=List[Supplier])
def get_rel_by_sku(sku: str):
    try:
        suppliers = supplierProduct_service.get_rel_by_sku(sku)
        return suppliers
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/by_supplier/{id}", response_model=List[Product])
def get_rel_by_id(id: int):
    try:
        products = supplierProduct_service.get_rel_by_supplier_id(id)
        return products
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=SupplierProduct, status_code=201)
def create_rel(supplier_product: SupplierProduct):
    try:
        rel = supplierProduct_service.create_rel(
            supplier_product.supplier_id, supplier_product.sku
        )
        return rel
    except DuplicateResourceError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{supplier_id}/{product_sku}", status_code=204)
def delete_rel(supplier_id: int, product_sku: str):
    try:
        supplierProduct_service.delete_rel(supplier_id, product_sku)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/supplier_recommendations", response_model=List[Supplier])
def get_recommendations(sku: str):
    try:
        suppliers = supplierProduct_service.recommend_suppliers(sku)
        return suppliers
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
