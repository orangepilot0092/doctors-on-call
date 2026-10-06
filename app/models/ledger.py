
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    entity_type = Column(String, nullable=False)  # 'hospital', 'doctor', 'platform', 'escrow'
    entity_id = Column(Integer, nullable=False)   # ID of hospital, doctor, or 0 for platform
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False) # 'HOLD', 'RELEASE', 'FEE', 'REFUND'
    razorpay_id = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
