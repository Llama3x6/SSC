from fastapi import FastAPI

from routers import orders, products, supplier_product_rel, suppliers

app = FastAPI(
    title="Sentient Supply Chain Mock ERP",
    description="Internal API for inventory, suppliers, and orders.",
    version="0.3.0",
)

app.include_router(products.router)
app.include_router(suppliers.router)
app.include_router(orders.router)
app.include_router(supplier_product_rel.router)
