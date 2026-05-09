from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(20), unique=True, index=True)   # CUST-0001
    company_name = Column(String(150), nullable=False)
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(30))
    country = Column(String(80))
    city = Column(String(80))
    address = Column(Text)
    payment_terms = Column(String(50))                             # Net 30, LC, TT Advance, etc.
    status = Column(String(20), default="active")                  # active | inactive
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders          = relationship("Order", back_populates="customer")
    customer_brands = relationship("CustomerBrand", back_populates="customer",
                                   cascade="all, delete-orphan")
