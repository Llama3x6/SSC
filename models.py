from ast import pattern
from pydantic import BaseModel, Field, PositiveInt, condecimal
from datetime import date
from typing import Optional



class Supplier(BaseModel):
    id: PositiveInt
    name: str = Field(..., min_length=1, max_length=100)
    reliability_score: float = Field(ge=0.0, le=1.0, default=1.0)
    contract_valid_until: date


class Product(BaseModel):
    sku: str = Field(..., pattern=r'^[A-Z]{3} - [0-9]{6}$')
    name: str
    current_stock: int = Field(ge=0, default=0)
    reorder_threshold: PositiveInt #probbly make it a f() of like EOQ
    #deeppity says:: # ENGINEERING LESSON: Using `ge` (greater than or equal) prevents invalid business states.


class Order(BaseModel):
    id: Optional[PositiveInt] = None #set by db not user
    product_sku: str
    quantity: PositiveInt
    order_date: date = Field(default_factory=date.today)
    status: str = Field(default="drafted", pattern='^(drafted|confirmed|shipped|cencelled)$' )
