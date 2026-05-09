from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class CustomerBrand(Base):
    """Many-to-many junction: a Brand can belong to multiple Customers and vice-versa."""
    __tablename__ = "customer_brands"

    id          = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    brand_id    = Column(Integer, ForeignKey("brands.id",    ondelete="CASCADE"), nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("customer_id", "brand_id", name="uq_customer_brand"),)

    customer = relationship("Customer", back_populates="customer_brands")
    brand    = relationship("Brand",    back_populates="customer_brands")


class Brand(Base):
    __tablename__ = "brands"

    id          = Column(Integer, primary_key=True, index=True)
    brand_code  = Column(String(20),  unique=True, index=True)   # BRD-0001
    brand_name  = Column(String(150), nullable=False)
    description = Column(Text)
    website     = Column(String(200))
    status      = Column(String(20), default="active")            # active | inactive
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Many-to-many with Customer (via CustomerBrand)
    customer_brands = relationship("CustomerBrand", back_populates="brand",
                                   cascade="all, delete-orphan")

    # One-to-many: styles created under this brand
    styles = relationship("GarmentStyle", back_populates="brand")

    @property
    def customers(self):
        return [cb.customer for cb in self.customer_brands]

    @property
    def customer_ids(self):
        return [cb.customer_id for cb in self.customer_brands]
