import enum
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Enum as SAEnum, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=True)
    specialization = Column(String, nullable=False)
    nmc_registration = Column(String, nullable=True)
    base_location = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    preferred_zones = Column(JSONB, nullable=True)
    daily_rate = Column(Numeric, nullable=False, default=3500.00)
    
    # Verification & Status
    verification_status = Column(SAEnum(VerificationStatus), default=VerificationStatus.PENDING)
    is_active = Column(Boolean, default=True)
    
    # Availability: {"2026-10-05": "free", "2026-10-06": "busy"}
    availability_calendar = Column(JSONB, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
