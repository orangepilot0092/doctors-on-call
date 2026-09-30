import enum
import uuid
from sqlalchemy import Column, String, DateTime, Integer, Float, Enum as SAEnum, Text, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.database import Base


class ShiftStatus(str, enum.Enum):
    PENDING = "pending"
    MATCHING = "matching"
    DOCTOR_NOTIFIED = "notified"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ShiftRequest(Base):
    __tablename__ = "shift_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_name = Column(String, nullable=False)
    clinic_pincode = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    shift_date = Column(String, nullable=False)
    shift_time = Column(String, nullable=False)
    status = Column(SAEnum(ShiftStatus), default=ShiftStatus.PENDING, nullable=False)
    
    # Assigned Doctor
    assigned_doctor_id = Column(UUID(as_uuid=True), nullable=True)
    assigned_doctor_name = Column(String, nullable=True)

    # Financial Tracking (Pre-Seed Ledger)
    clinic_charge = Column(Numeric, nullable=True)  # What clinic pays
    doctor_payout = Column(Numeric, nullable=True)  # What doctor gets
    platform_margin = Column(Numeric, nullable=True)  # clinic_charge - doctor_payout
    
    # Validation Command Center tracking fields
    reason_posted = Column(String, nullable=True)
    current_sourcing_method = Column(String, nullable=True)
    doctors_contacted_count = Column(Integer, default=0)
    time_to_fill_minutes = Column(Integer, nullable=True)
    
    # Feedback
    clinic_satisfaction = Column(Integer, nullable=True)  # 1-5 rating
    would_use_again = Column(Boolean, nullable=True)
    would_pay_platform_fee = Column(Boolean, nullable=True)
    max_acceptable_fee = Column(Numeric, nullable=True)
    feedback_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
