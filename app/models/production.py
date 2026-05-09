from sqlalchemy import Column, Integer, String, DateTime, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from ..database import Base


class Production(Base):
    __tablename__ = "productions"

    id = Column(Integer, primary_key=True, index=True)
    production_no = Column(String(30), unique=True, index=True)    # PRD-2025050001
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    line_id = Column(Integer, ForeignKey("production_lines.id"), nullable=False)
    planned_start = Column(Date)
    planned_end = Column(Date)
    actual_start = Column(Date)
    actual_end = Column(Date)
    planned_qty = Column(Integer, nullable=False)                   # Quantity allocated to this run
    output_qty = Column(Integer, default=0)                        # Actual produced (passed)
    rejected_qty = Column(Integer, default=0)                      # QC rejected
    remarks = Column(Text)
    status = Column(String(30), default="scheduled")
    # scheduled | in_progress | completed | on_hold | cancelled

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship("Order", back_populates="productions")
    line = relationship("ProductionLine", back_populates="productions")

    @property
    def efficiency(self):
        if self.planned_qty and self.planned_qty > 0:
            return round((self.output_qty or 0) / self.planned_qty * 100, 1)
        return 0
