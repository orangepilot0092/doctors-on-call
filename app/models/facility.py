from sqlalchemy import Column, Integer, String, Float, Boolean, JSON
from app.db.base import Base

class Facility(Base):
    __tablename__ = "facilities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    
    # Core Location & Transit
    location_area = Column(String, nullable=False, index=True, default="MMR")
    transit_corridor = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Commercial Dataset Fields
    address = Column(String, nullable=True)
    city = Column(String, nullable=True, default="Mumbai")
    state = Column(String, nullable=True, default="Maharashtra")
    pin_code = Column(String, nullable=True, index=True)
    landline = Column(String, nullable=True)
    mobile = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # 🆕 Two-Sided Trust: Hospital Verification Fields
    is_verified = Column(Boolean, default=False, index=True)
    authorized_contact_name = Column(String, nullable=True)
    authorized_contact_phone = Column(String, nullable=True)
    gst_number = Column(String, nullable=True)
    verified_at = Column(String, nullable=True) # Timestamp of verification
    
    # ABDM & Internal Fields
    abdm_facility_id = Column(String, unique=True, nullable=True)
    departments = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
