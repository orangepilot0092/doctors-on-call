from pydantic import BaseModel, Field
from typing import Optional, Literal

class HospitalMetadata(BaseModel):
    name: Optional[str] = None
    location_area: Optional[str] = None
    department: Optional[str] = None

class ShiftDetails(BaseModel):
    role_required: Optional[Literal["RMO", "Consultant", "Staff Nurse", "Intensivist", "Technician"]] = None
    specialty: Optional[str] = None
    date_raw: Optional[str] = None
    shift_type: Optional[Literal["Day", "Night", "24-Hour", "Custom"]] = None
    estimated_hours: Optional[int] = None
    urgency_level: Literal["CRITICAL", "HIGH", "ROUTINE"] = "ROUTINE"

class Financials(BaseModel):
    offered_rate_inr: Optional[int] = None
    rate_basis: Optional[Literal["per_hour", "per_shift", "per_day"]] = None

class ComplianceFlags(BaseModel):
    required_registration: Optional[Literal["MMC", "MNC"]] = None
    gender_preference: Literal["Female", "Male", "None"] = "None"

class ShiftExtractionRequest(BaseModel):
    raw_text: str = Field(..., description="The chaotic hospital message to parse")

class ShiftExtractionResponse(BaseModel):
    hospital_metadata: HospitalMetadata
    shift_details: ShiftDetails
    financials: Financials
    compliance_flags: ComplianceFlags
