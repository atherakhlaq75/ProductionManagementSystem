from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class ProductionLine(Base):
    __tablename__ = "production_lines"

    id = Column(Integer, primary_key=True, index=True)
    line_code = Column(String(20), unique=True, index=True)        # LINE-01
    line_name = Column(String(100), nullable=False)                # Sewing Line A
    floor = Column(String(50))                                     # Floor 1, Floor 2, etc.
    capacity_per_day = Column(Integer)                             # Target pieces per day
    operator_count = Column(Integer)                               # Number of operators
    supervisor = Column(String(100))                               # Line supervisor name
    line_type = Column(String(50))                                 # Sewing, Finishing, Cutting, etc.
    description = Column(Text)
    status = Column(String(20), default="active")                  # active | inactive | maintenance
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    productions = relationship("Production", back_populates="line")
