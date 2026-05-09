from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from ..database import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(30), unique=True, index=True)       # INV-2025050001
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    shipment_date = Column(Date, default=date.today)
    shipped_qty = Column(Integer, nullable=False)
    carton_count = Column(Integer)
    net_weight_kg = Column(Numeric(10, 2))
    gross_weight_kg = Column(Numeric(10, 2))
    unit_price = Column(Numeric(12, 4))                            # Confirmed invoice price
    currency = Column(String(10), default="USD")
    port_of_loading = Column(String(100))
    port_of_discharge = Column(String(100))
    vessel_name = Column(String(150))
    bl_number = Column(String(100))                                # Bill of Lading
    etd = Column(Date)                                             # Estimated Time of Departure
    eta = Column(Date)                                             # Estimated Time of Arrival
    remarks = Column(Text)
    status = Column(String(30), default="draft")
    # draft | confirmed | shipped | delivered

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship("Order", back_populates="shipments")

    @property
    def invoice_value(self):
        return round(float(self.unit_price or 0) * (self.shipped_qty or 0), 2)
