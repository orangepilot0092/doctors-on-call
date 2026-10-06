
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    invoice_type = Column(String, nullable=False)  # 'PLATFORM_FEE', 'DOCTOR_PAYOUT'
    entity_id = Column(Integer, nullable=False)    # Hospital ID or Doctor ID
    base_amount = Column(Float, nullable=False)
    gst_amount = Column(Float, nullable=False)     # 18% on platform fee
    tds_amount = Column(Float, nullable=False)     # e.g., 2% on doctor payout
    final_amount = Column(Float, nullable=False)
    invoice_number = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
