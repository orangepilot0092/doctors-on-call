from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid


class DoctorCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=10)
    email: Optional[str] = None
    specialization: str = Field(..., min_length=2)
    nmc_registration: Optional[str] = None
    base_location: str = Field(..., min_length=2)
    pincode: str = Field(..., min_length=6, max_length=6)
    preferred_zones: Optional[List[str]] = None
    daily_rate: float = Field(default=3500.0, ge=0)
    availability_calendar: Optional[Dict[str, str]] = None


class DoctorResponse(BaseModel):
    id: uuid.UUID
    name: str
    specialization: str
    verification_status: str
    message: Optional[str] = None
    phone: Optional[str] = None
    base_location: Optional[str] = None
    daily_rate: Optional[float] = None

    class Config:
        from_attributes = True


class DoctorAvailabilityUpdate(BaseModel):
    availability_calendar: Dict[str, str]  # {"2026-10-05": "free", "2026-10-06": "busy"}
