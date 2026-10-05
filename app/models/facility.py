from sqlalchemy import Column, Integer, String, Float, Boolean, JSON
from app.db.base import Base

class Facility(Base):
    __tablename__ = "facilities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    
    # Mumbai MMR Specifics
    location_area = Column(String, nullable=False, index=True)  # e.g., "Andheri West", "Thane", "Vashi"
    transit_corridor = Column(String, nullable=True)  # "Western Line", "Central Line", "Harbour Line", "Road"
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # ABDM Facility Mapping (Optional)
    abdm_facility_id = Column(String, unique=True, nullable=True)  # e.g., "IN2710000059"
    
    departments = Column(JSON, nullable=True)  # e.g., ["ICU", "ER", "General Ward"]
    is_active = Column(Boolean, default=True)
