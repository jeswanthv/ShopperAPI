from sqlalchemy import Column, Integer, String, BigInteger, Float, ForeignKey
from .database import Base


class Product(Base):
    __tablename__ = "products"

    # This is the ID from the Product Service (Elasticsearch)
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, index=True)
    order_id = Column(BigInteger, unique=True, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="PENDING")

    # This would be the ID from the payment provider (e.g., Stripe)
    payment_gateway_id = Column(String, index=True)
