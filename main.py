from fastapi import FastAPI, HTTPException, status
from models import Product, Supplier, Order
from typing import List
from datetime import date

app = FastAPI(
    title="Sentient Supply Chain Mock ERP",
    description="Internal API for inventory, suppliers, and orders.",
    version="0.1.0"
)




####==================== Product Data and Endpoints ====================###

# Temporary in-memory storage for products
# In a real system, this would be a database.
products_db = {}


# Seed some dummy data so we have something to query
products_db["ABC-123456"] = Product(
    sku="ABC-123456",
    name="Test Widget",
    current_stock=100,
    reorder_threshold=20
)
products_db["XYZ-789012"] = Product(
    sku="XYZ-789012",
    name="Test Gadget",
    current_stock=5,
    reorder_threshold=10
)


######---------------------- Product Endpoints -----------------------######


@app.get("/")
def root():
    return {"message": "Supply Chain Mock ERP is alive. Go to /docs for interactive documentation."}

@app.get("/products", response_model=List[Product])
def list_products():
    """Return all products in the system."""
    return list(products_db.values())

@app.get("/products/{sku}", response_model=Product)
def get_product(sku: str):
    """Return a single product by its SKU."""
    if sku not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[sku]


@app.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(product: Product):
    """
    Add a new product to the inventory.
    - The request body must match the Product schema.
    - If a product with the same SKU already exists, returns 400.
    """
    if product.sku in products_db:
        raise HTTPException(
            status_code=400,
            detail=f"Product with SKU '{product.sku}' already exists"
        )
    products_db[product.sku] = product
    return product


@app.put("/products/{sku}", response_model=Product)
def update_product(sku: str, updated_product: Product):
    """
    Fully replace an existing product.
    - The SKU in the URL must match the SKU in the request body.
    - If the product doesn't exist, returns 404.
    """
    if sku not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    # Ensure the SKU in the body matches the URL (optional but good practice)
    if updated_product.sku != sku:
        raise HTTPException(status_code=400, detail="SKU in URL and body must match")
    products_db[sku] = updated_product
    return updated_product


@app.delete("/products/{sku}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(sku: str):
    """
    Remove a product from inventory.
    - Returns 204 No Content on success.
    - If the product doesn't exist, returns 404.
    """
    if sku not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    del products_db[sku]
    # No content returned, just a successful empty response
    return None







###==================== Supplier Data and Endpoints ====================###

suppliers_db = {}
next_supplier_id = 1  # Simple auto‑increment


# Seed some suppliers
suppliers_db[1] = Supplier(id=1, name="LogiCo AG", reliability_score=0.95, contract_valid_until=date(2025,12,31))
suppliers_db[2] = Supplier(id=2, name="Parts GmbH", reliability_score=0.82, contract_valid_until=date(2024,6,30))
next_supplier_id = 3


######---------------------- Supplier Endpoints -----------------------######

@app.get("/suppliers", response_model=List[Supplier])
def list_suppliers():
    """Return all suppliers."""
    return list(suppliers_db.values())

@app.get("/suppliers/{supplier_id}", response_model=Supplier)
def get_supplier(supplier_id: int):
    """Return a single supplier by ID."""
    if supplier_id not in suppliers_db:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return suppliers_db[supplier_id]




@app.post("/suppliers", response_model=Supplier, status_code=status.HTTP_201_CREATED)
def create_supplier(supplier: Supplier):
    """
    Create a new supplier.
    The 'id' field in the request body is ignored; a new ID is generated.
    """
    global next_supplier_id
    # Ensure the supplier has no ID (or ignore it)
    supplier.id = next_supplier_id
    # Check for duplicate name? (optional, but could be useful)
    for existing in suppliers_db.values():
        if existing.name == supplier.name:
            raise HTTPException(status_code=400, detail="Supplier with this name already exists")
    suppliers_db[next_supplier_id] = supplier
    next_supplier_id += 1
    return supplier

@app.put("/suppliers/{supplier_id}", response_model=Supplier)
def update_supplier(supplier_id: int, updated_supplier: Supplier):
    """Replace an existing supplier."""
    if supplier_id not in suppliers_db:
        raise HTTPException(status_code=404, detail="Supplier not found")
    # Ensure the ID in the body matches the URL (or ignore it)
    if updated_supplier.id != supplier_id:
        # Option 1: force the ID to match
        updated_supplier.id = supplier_id
        # Option 2: raise error – we'll go with forcing it silently
    suppliers_db[supplier_id] = updated_supplier
    return updated_supplier

@app.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(supplier_id: int):
    """Delete a supplier."""
    if supplier_id not in suppliers_db:
        raise HTTPException(status_code=404, detail="Supplier not found")
    del suppliers_db[supplier_id]
    return None


###==================== Order Data and Endpoints ====================###


# In-memory storage for orders
orders_db = {}
next_order_id = 1


# Seed a few orders (assuming products ABC-123456 and XYZ-789012 exist)
orders_db[1] = Order(id=1, product_sku="ABC-123456", quantity=10, status="drafted")
orders_db[2] = Order(id=2, product_sku="XYZ-789012", quantity=5, status="confirmed")
next_order_id = 3

#####---------------------- Order Endpoints -----------------------######


@app.get("/orders", response_model=List[Order])
def list_orders():
    """Return all orders."""
    return list(orders_db.values())

@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    """Return a single order by ID."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]

@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_order(order: Order):
    """
    Create a new order.
    - The 'id' field is ignored; a new ID is generated.
    - 'product_sku' must reference an existing product.
    - 'status' defaults to 'drafted' if not provided.
    """
    global next_order_id
    # Validate product exists
    if order.product_sku not in products_db:
        raise HTTPException(status_code=400, detail=f"Product with SKU '{order.product_sku}' does not exist")
    # Assign ID and store
    order.id = next_order_id
    orders_db[next_order_id] = order
    next_order_id += 1
    return order

@app.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: int, updated_order: Order):
    """Replace an existing order."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    # Validate product exists
    if updated_order.product_sku not in products_db:
        raise HTTPException(status_code=400, detail=f"Product with SKU '{updated_order.product_sku}' does not exist")
    # Ensure ID consistency
    updated_order.id = order_id
    orders_db[order_id] = updated_order
    return updated_order

@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int):
    """Delete an order."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    del orders_db[order_id]
    return None

# Optional: Endpoint to transition order status (if you want a more controlled state machine)
@app.patch("/orders/{order_id}/status", response_model=Order)
def change_order_status(order_id: int, new_status: str):
    """
    Update only the status of an order.
    This is a simple example; you could add validation for allowed transitions.
    """
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    order = orders_db[order_id]
    # Optional: check if transition is allowed (e.g., drafted -> confirmed, but not shipped -> drafted)
    # For now, just set it.
    if new_status not in ["drafted", "confirmed", "shipped", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    order.status = new_status
    orders_db[order_id] = order
    return order
