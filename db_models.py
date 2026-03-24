from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String

from database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=True)
    reliability_score = Column(Float, nullable=False)
    contract_valid_until = Column(Date, nullable=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    current_stock = Column(Integer, nullable=False)
    reorder_threshold = Column(Integer, nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    product_sku = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    order_date = Column(Date, nullable=False)
    status = Column(String, nullable=False)


# Association table for many-to-many relationship between suppliers and products
class SupplierProduct(Base):
    __tablename__ = "supplier_products"

    supplier_id = Column(Integer, ForeignKey("suppliers.id"), primary_key=True)
    sku = Column(String, ForeignKey("products.sku"), primary_key=True)
