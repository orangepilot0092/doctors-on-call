from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any

class FacilityDeclarationData(BaseModel):
    facilityId: Optional[str] = None
    facilityName: Optional[str] = None
    facilityAddress: Optional[str] = None
    facilityPincode: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    facilityType: Optional[str] = None
    facilityDepartment: Optional[str] = None
    facilityDesignation: Optional[str] = None
    ministry: Optional[Dict[str, str]] = None

class CurrentWorkDetails(BaseModel):
    currentlyWorking: str
    purposeOfWork: str
    chooseWorkStatus: int  # 0: Private, 1: Government, 2: Both
    reasonForNotWorking: Optional[str] = ""
    certificateAttachment: Optional[str] = ""
    facilityDeclarationData: Optional[FacilityDeclarationData] = None

    @model_validator(mode='after')
    def validate_work_status(self) -> 'CurrentWorkDetails':
        if self.chooseWorkStatus in [1, 2]:
            if not self.facilityDeclarationData:
                raise ValueError("facilityDeclarationData is mandatory for Government (1) or Both (2) work status.")
        elif self.chooseWorkStatus == 0:
            # Explicitly remove it if Private to satisfy ABDM strict payload validation
            self.facilityDeclarationData = None
        return self

class UpdateProfessionalRequest(BaseModel):
    hprToken: str = Field(..., alias="hpr_token")
    practitioner: Dict[str, Any]
    currentWorkDetails: CurrentWorkDetails

    class Config:
        populate_by_name = True
