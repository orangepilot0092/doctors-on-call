from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class ShiftCreateRequest(BaseModel):
    clinic_name: str = Field(..., min_length=2, max_length=100)
    clinic_pincode: str = Field(..., min_length=6, max_length=6)
    specialty: str = Field(..., min_length=2, max_length=100)
    shift_date: str = Field(..., description="Format: YYYY-MM-DD")
    shift_time: str = Field(..., description="e.g., 09:00 AM - 05:00 PM")
    reason_posted: Optional[str] = None
    current_sourcing_method: Optional[str] = None


class ShiftResponse(BaseModel):
    id: uuid.UUID
    status: str
    message: str

    class Config:
        from_attributes = True


class ShiftStatusResponse(BaseModel):
    id: uuid.UUID
    clinic_name: str
    clinic_pincode: str
    specialty: str
    shift_date: str
    shift_time: str
    status: str
    doctors_contacted_count: int
    time_to_fill_minutes: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
