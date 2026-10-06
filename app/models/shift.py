from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.db.base import Base
import enum

class UrgencyLevel(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    ROUTINE = "ROUTINE"

class ShiftStatus(str, enum.Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Shift(Base):
    __tablename__ = "shifts"
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    check_in_lat = Column(Float, nullable=True)
    check_in_lon = Column(Float, nullable=True)
    check_out_lat = Column(Float, nullable=True)
    check_out_lon = Column(Float, nullable=True)
    assigned_doctor_id = Column(Integer, nullable=True)
    required_specialty = Column(String, nullable=True)
    
    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    title = Column(String, nullable=True)
    
    # Shift Details
    role_required = Column(String, nullable=False)  # "RMO", "Staff Nurse", "Consultant"
    specialty = Column(String, nullable=True)
    department = Column(String, nullable=False)
    
    # Time
    date_raw = Column(String, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    estimated_hours = Column(Integer, nullable=True)
    
    # Financials
    offered_rate_inr = Column(Integer, nullable=False)
    rate_basis = Column(String, nullable=False)  # "per_hour", "per_shift", "per_day"
    
    # Metadata
    urgency_level = Column(Enum(UrgencyLevel), default=UrgencyLevel.ROUTINE)
    status = Column(Enum(ShiftStatus), default=ShiftStatus.OPEN)
    
    # Compliance
    requires_mmc = Column(Boolean, default=False)
    requires_mnc = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
