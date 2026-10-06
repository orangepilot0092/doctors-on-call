
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True, index=True)
    hospital_id = Column(Integer, nullable=True, index=True)

    dispute_type = Column(String, nullable=False)
    # Examples: NO_SHOW, EARLY_DEPARTURE, QUALITY_OF_CARE, PAYMENT_ISSUE

    status = Column(String, nullable=False, default="OPEN", index=True)
    # Examples: OPEN, UNDER_REVIEW, REFUNDED, PARTIAL_REFUND, REJECTED, RESOLVED

    amount_claimed = Column(Float, nullable=True)
    amount_refunded = Column(Float, nullable=True)

    notes = Column(String, nullable=True)
    resolution_notes = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
