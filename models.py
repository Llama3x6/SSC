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


# =============================================================================================
# LLM Output Schemas (structured outputs)
# =============================================================================================


class ReorderNarrative(BaseModel):
    """Structured output for HITL reorder approval narrative."""

    summary: str = Field(
        ..., description="Brief summary of the reorder proposal (1-2 sentences)"
    )
    low_products: list[str] = Field(
        ...,
        description="List of SKUs that are below reorder threshold with stock levels",
    )
    proposed_orders: list[str] = Field(
        ...,
        description="List of proposed orders with supplier and quantity",
    )
    risk_flags: list[str] = Field(
        default_factory=list,
        description="Any risk flags or concerns (empty if none)",
    )
    recommendation: str = Field(
        ...,
        description="Clear recommendation: 'approve', 'review_first', or 'reject_and_reason'",
    )


class ShiftReportItem(BaseModel):
    """Item in a shift report."""

    category: str = Field(
        ..., description="Category (e.g., 'recent_orders', 'low_stock', 'expiring_contracts')"
    )
    items: list[str] = Field(..., description="List of items in this category")


class ShiftReport(BaseModel):
    """Structured shift report output."""

    timestamp: str = Field(
        ..., description="ISO-formatted timestamp when report was generated"
    )
    summary: str = Field(..., description="Executive summary of shift status")
    sections: list[ShiftReportItem] = Field(
        ..., description="Report sections with categorized items"
    )
    alerts: list[str] = Field(
        default_factory=list,
        description="High-priority alerts requiring immediate action",
    )


class RiskCountry(BaseModel):
    """Country-level risk assessment."""

    country: str = Field(..., description="Country name")
    suppliers: list[str] = Field(..., description="Suppliers in this country")
    risk_level: str = Field(
        ..., description="Risk level: 'low', 'medium', or 'high'"
    )
    concerns: list[str] = Field(
        ..., description="Specific geopolitical concerns for this country"
    )


class GeopoliticalRiskDigest(BaseModel):
    """Structured geopolitical risk digest output."""

    timestamp: str = Field(
        ..., description="ISO-formatted timestamp when report was generated"
    )
    summary: str = Field(
        ...,
        description="Executive summary of overall supply chain geopolitical risk",
    )
    countries: list[RiskCountry] = Field(
        ..., description="Risk assessment per country"
    )
    actionable_items: list[str] = Field(
        ...,
        description="Specific actionable recommendations for supply chain mitigation",
    )
