from sqlalchemy import Column, Integer, String, BigInteger, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, index=True)
    account_id = Column(BigInteger, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="PENDING")

    # This creates the one-to-many relationship
    products = relationship("OrderedProduct", back_populates="order")


class OrderedProduct(Base):
    __tablename__ = "ordered_products"

    id = Column(BigInteger, primary_key=True, index=True)
    product_id = Column(String, nullable=False)  # The ID from Elasticsearch
    quantity = Column(Integer, nullable=False)
    order_id = Column(BigInteger, ForeignKey("orders.id"))

    order = relationship("Order", back_populates="products")
