from sqlalchemy import Column, Integer, String, Float, Boolean, JSON
from app.db.base import Base

class Facility(Base):
    __tablename__ = "facilities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    
    # Mumbai MMR Specifics
    location_area = Column(String, nullable=False, index=True, default="MMR")
    transit_corridor = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # ABDM Facility Mapping
    abdm_facility_id = Column(String, unique=True, nullable=True)
    
    departments = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
