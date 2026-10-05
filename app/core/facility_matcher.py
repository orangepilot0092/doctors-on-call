"""
Fuzzy Facility Matcher - Matches extracted hospital names against
the PostgreSQL database of ALL MMR hospitals.
Uses difflib for fuzzy string matching.
"""
import difflib
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from app.models.facility import Facility

class FacilityMatcher:
    """Matches extracted hospital names against the database."""
    
    def __init__(self):
        self._cache: List[Dict[str, Any]] = []
        self._cache_loaded = False
    
    async def load_facilities(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Load all facilities from DB into memory for fast matching."""
        if self._cache_loaded and self._cache:
            return self._cache
        
        result = await db.execute(select(Facility).where(Facility.is_active == True))
        facilities = result.scalars().all()
        
        self._cache = [
            {
                "id": f.id,
                "name": f.name,
                "name_lower": f.name.lower(),
                "location_area": f.location_area,
                "transit_corridor": f.transit_corridor,
                "latitude": f.latitude,
                "longitude": f.longitude,
            }
            for f in facilities
        ]
        self._cache_loaded = True
        return self._cache
    
    async def match(self, db: AsyncSession, extracted_name: str, location_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fuzzy match an extracted hospital name against the database.
        Returns the best match or None.
        """
        facilities = await self.load_facilities(db)
        
        if not facilities:
            return None
        
        extracted_lower = extracted_name.lower().strip()
        
        # 1. Exact match first
        for f in facilities:
            if extracted_lower == f["name_lower"]:
                return f
        
        # 2. Fuzzy match using difflib
        best_match = None
        best_score = 0.0
        THRESHOLD = 0.6  # 60% similarity threshold
        
        for f in facilities:
            score = difflib.SequenceMatcher(None, extracted_lower, f["name_lower"]).ratio()
            
            # Boost score if location matches
            if location_hint and f["location_area"]:
                if location_hint.lower() in f["location_area"].lower():
                    score += 0.15
            
            if score > best_score:
                best_score = score
                best_match = f
        
        if best_score >= THRESHOLD and best_match:
            return best_match
        
        return None
    
    def invalidate_cache(self):
        """Clear the cache (call when new facilities are added)."""
        self._cache = []
        self._cache_loaded = False

# Singleton
facility_matcher = FacilityMatcher()
