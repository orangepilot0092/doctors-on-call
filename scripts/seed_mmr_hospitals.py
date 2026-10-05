import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.facility import Facility

# MMR overall bounds
MIN_LAT, MAX_LAT = 18.85, 19.50
MIN_LON, MAX_LON = 72.75, 73.20

# Split into a 6x5 grid (30 micro-zones) to prevent Overpass 504 Timeouts
GRID_LAT = 6
GRID_LON = 5
LAT_STEP = (MAX_LAT - MIN_LAT) / GRID_LAT
LON_STEP = (MAX_LON - MIN_LON) / GRID_LON

OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
]

# Broadest possible query to catch hospitals, clinics, nursing homes, and doctors
OVERPASS_QUERY = """
[out:json][timeout:90];
(
  node["amenity"~"^(hospital|clinic|doctors|nursing_home)$"]({bbox});
  way["amenity"~"^(hospital|clinic|doctors|nursing_home)$"]({bbox});
  node["healthcare"~"^(hospital|clinic|centre|doctor|nurse|midwife|physiotherapist|laboratory)$"]({bbox});
  way["healthcare"~"^(hospital|clinic|centre|doctor|nurse|midwife|physiotherapist|laboratory)$"]({bbox});
);
out center tags;
"""

def get_transit_corridor(lat, lon):
    if not lat or not lon: return "Road"
    if lon < 72.86 and lat > 18.92: return "Western Line"
    if 72.86 <= lon <= 73.05 and lat > 19.00: return "Central Line"
    if lon > 72.95 and lat < 19.05: return "Harbour Line"
    if lon > 72.95 and lat > 19.15: return "Central Line"
    if 72.90 <= lon <= 73.00 and 19.05 <= lat <= 19.15: return "Trans-Harbour"
    return "Road"

def get_location_area(tags):
    for k in ["addr:suburb", "addr:neighbourhood", "addr:city", "addr:district"]:
        if k in tags: return tags[k]
    return "MMR"

async def fetch_zone(client, bbox_str, zone_name):
    query = OVERPASS_QUERY.format(bbox=bbox_str)
    for mirror in OVERPASS_MIRRORS:
        try:
            resp = await client.post(mirror, data={"data": query}, headers={"User-Agent": "DoctorsOnCall/2.0"})
            if resp.status_code == 200:
                return resp.json().get("elements", [])
        except Exception:
            continue
    return []

async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    print("="*60)
    print("🏥 MMR Micro-Grid OSM Seeder (30 Zones)")
    print("="*60)
    
    all_elements = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        for i in range(GRID_LAT):
            for j in range(GRID_LON):
                s_lat = MIN_LAT + i * LAT_STEP
                n_lat = s_lat + LAT_STEP
                w_lon = MIN_LON + j * LON_STEP
                e_lon = w_lon + LON_STEP
                bbox_str = f"{s_lat},{w_lon},{n_lat},{e_lon}"
                zone_name = f"Zone {i*GRID_LON + j + 1}"
                
                elements = await fetch_zone(client, bbox_str, zone_name)
                print(f"✅ {zone_name}: Found {len(elements)} facilities")
                all_elements.extend(elements)
                await asyncio.sleep(2) # Be polite to the API
                
    print(f"\n📊 Total raw elements fetched: {len(all_elements)}")
    
    # Deduplicate by name + approximate location
    seen = set()
    to_insert = []
    
    async with AsyncSessionLocal() as session:
        # Get existing names to avoid duplicates on re-run
        result = await session.execute(select(Facility.name))
        existing_names = {row[0].lower() for row in result.all()}
        
        for elem in all_elements:
            tags = elem.get("tags", {})
            name = tags.get("name", "").strip()
            if not name or name.lower() in existing_names:
                continue
                
            # Basic deduplication for this batch
            if name.lower() in seen:
                continue
            seen.add(name.lower())
            
            if elem["type"] == "node":
                lat, lon = elem.get("lat"), elem.get("lon")
            else:
                center = elem.get("center", {})
                lat, lon = center.get("lat"), center.get("lon")
                
            to_insert.append(Facility(
                name=name,
                location_area=get_location_area(tags),
                transit_corridor=get_transit_corridor(lat, lon),
                latitude=lat,
                longitude=lon
            ))
            
        print(f"💾 Inserting {len(to_insert)} new unique facilities into PostgreSQL...")
        if to_insert:
            session.add_all(to_insert)
            await session.commit()
            print(f"✅ Successfully committed {len(to_insert)} facilities!")
        else:
            print("ℹ️ No new facilities to insert.")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
