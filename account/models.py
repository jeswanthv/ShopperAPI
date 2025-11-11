from sqlalchemy import Column, Integer, String, BigInteger
from .database import Base


class Account(Base):
    __tablename__ = "accounts"

    # Use BigInteger to match the 'uint64' from the proto
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # This will store the hash
