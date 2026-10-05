import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.facility import Facility
from app.db.session import get_db

router = APIRouter(prefix="/bulk", tags=["Bulk Data Ingestion"])

@router.post("/facilities-csv")
async def import_facilities_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Bulk import hospitals/clinics from a CSV file.
    Expected CSV columns: name, location_area, transit_corridor, latitude, longitude
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
        
    contents = await file.read()
    decoded = contents.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    count = 0
    for row in reader:
        name = row.get('name', '').strip()
        if not name:
            continue
            
        facility = Facility(
            name=name,
            location_area=row.get('location_area', 'MMR'),
            transit_corridor=row.get('transit_corridor', 'Road'),
            latitude=float(row['latitude']) if row.get('latitude') else None,
            longitude=float(row['longitude']) if row.get('longitude') else None
        )
        db.add(facility)
        count += 1
        
    await db.commit()
    return {"status": "success", "imported": count}
