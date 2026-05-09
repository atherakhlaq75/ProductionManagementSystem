from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class GarmentStyle(Base):
    __tablename__ = "garment_styles"

    id = Column(Integer, primary_key=True, index=True)
    style_no = Column(String(50), unique=True, index=True)         # STY-2025-0001
    style_name = Column(String(150), nullable=False)
    description = Column(Text)
    category = Column(String(80))                                   # Shirt, Trouser, Jacket, T-Shirt, etc.
    fabric_type = Column(String(100))                               # 100% Cotton, Polyester, Denim, etc.
    fabric_composition = Column(String(200))                        # 60% Cotton 40% Poly, etc.
    season = Column(String(50))                                     # SS25, AW25, etc.
    gender = Column(String(20))                                     # Men, Women, Kids, Unisex
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)  # specific buyer within brand
    buyer_style_ref = Column(String(100))                           # Buyer's own style reference
    unit_of_measure = Column(String(20), default="PCS")             # PCS, DOZ
    standard_cost = Column(Numeric(12, 2))                          # Production cost per unit
    standard_minutes = Column(Numeric(8, 2))                        # SAM (Standard Allowed Minutes)
    status = Column(String(20), default="active")                   # active | inactive | discontinued
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    brand    = relationship("Brand",    back_populates="styles", foreign_keys=[brand_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    orders   = relationship("Order",    back_populates="style")
