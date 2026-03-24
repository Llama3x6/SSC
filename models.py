from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, PositiveInt


class Supplier(BaseModel):
    id: Optional[PositiveInt] = None  # set by db not user
    name: str = Field(..., min_length=1, max_length=100)
    country: Optional[str] = Field(default=None, pattern=r"^[A-Z]{2}$")
    reliability_score: float = Field(ge=0.0, le=1.0, default=1.0)
    contract_valid_until: date


class Product(BaseModel):
    sku: str = Field(..., pattern=r"^[A-Z]{3}-[0-9]{6}$")  # No spaces
    name: str
    current_stock: int = Field(ge=0, default=0)
    reorder_threshold: PositiveInt  # probbly make it a f() of like EOQ
    # deeppity says:: # ENGINEERING LESSON: Using `ge` (greater than or equal) prevents invalid business states.


class Order(BaseModel):
    id: Optional[PositiveInt] = None  # set by db not user
    product_sku: str
    supplier_id: PositiveInt
    quantity: PositiveInt
    order_date: date = Field(default_factory=date.today)
    status: str = Field(
        default="drafted", pattern="^(drafted|confirmed|shipped|cancelled)$"
    )


class SupplierProduct(BaseModel):
    supplier_id: PositiveInt
    sku: str
