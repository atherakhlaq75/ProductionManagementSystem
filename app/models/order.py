from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from ..database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(30), unique=True, index=True)         # ORD-2025050001
    po_number = Column(String(100))                                # Buyer's Purchase Order number
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    style_id = Column(Integer, ForeignKey("garment_styles.id"), nullable=False)
    order_qty = Column(Integer, nullable=False)                    # Total ordered quantity
    unit_price = Column(Numeric(12, 4), nullable=False)            # Per piece / per dozen
    currency = Column(String(10), default="USD")
    order_date = Column(Date, default=date.today)
    delivery_date = Column(Date)                                   # Required ship date
    remarks = Column(Text)
    status = Column(String(30), default="pending")
    # pending | confirmed | in_production | ready_to_ship | shipped | cancelled

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="orders")
    style = relationship("GarmentStyle", back_populates="orders")
    productions = relationship("Production", back_populates="order")
    shipments = relationship("Shipment", back_populates="order")

    @property
    def total_value(self):
        return (self.order_qty or 0) * float(self.unit_price or 0)

    @property
    def produced_qty(self):
        return sum(p.output_qty or 0 for p in self.productions if p.status == "completed")

    @property
    def shipped_qty(self):
        return sum(s.shipped_qty or 0 for s in self.shipments)
