from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class UrgencyLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    ROUTINE = "ROUTINE"

class ShiftStatus(str, Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ShiftCreate(BaseModel):
    facility_id: int
    role_required: str
    department: str
    start_time: datetime
    end_time: datetime
    offered_rate_inr: int
    rate_basis: str
    specialty: Optional[str] = None
    estimated_hours: Optional[int] = None
    urgency_level: UrgencyLevel = UrgencyLevel.ROUTINE
    requires_mmc: bool = False
    requires_mnc: bool = False

class ShiftRead(BaseModel):
    id: int
    facility_id: int
    role_required: str
    department: str
    start_time: datetime
    end_time: datetime
    offered_rate_inr: int
    rate_basis: str
    specialty: Optional[str] = None
    estimated_hours: Optional[int] = None
    urgency_level: UrgencyLevel
    status: ShiftStatus
    requires_mmc: bool
    requires_mnc: bool
    created_at: datetime

    class Config:
        from_attributes = True
