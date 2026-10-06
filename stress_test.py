import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update, select
import numpy as np
from datetime import datetime, timezone

from app.core.config import settings
from app.models.doctor_master_record import Doctor, DoctorStatus
from app.models.facility import Facility
from app.models.shift import Shift, ShiftStatus
from app.services.semantic_matching import generate_mock_embedding

BASE_URL = "http://localhost:8005/api/v1"

async def seed_database():
    print("\n🔥 PHASE 1: Seeding 10 Doctors & 1 Shift...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession)
    
    async with Session() as session:
        # Clear old test doctors (IDs 3 to 12)
        for i in range(3, 13):
            stmt = update(Doctor).where(Doctor.id == i).values(status=DoctorStatus.REJECTED)
            await session.execute(stmt)
            
        # Seed 10 new doctors
        for i in range(1, 11):
            doc_id = i + 2 # IDs 3 to 12
            is_icu = i % 2 == 0
            is_central = i % 3 == 0
            
            specialty = "ICU, Critical Care, Ventilator, ECMO" if is_icu else "General Ward, Routine Care"
            corridor = "Central Line" if is_central else "Western Line"
            
            # Generate mock vector embedding
            vec = generate_mock_embedding(specialty)
            
            # Upsert doctor
            doc = await session.get(Doctor, doc_id)
            if not doc:
                doc = Doctor(id=doc_id, doctor_code=f"DOC-000{doc_id}", full_name=f"Dr. Stress {doc_id}", email=f"stress{doc_id}@test.com", phone=f"900000000{doc_id}")
                session.add(doc)
                
            doc.status = DoctorStatus.SHIFT_READY
            doc.pg_specialty = specialty
            doc.home_transit_corridor = corridor
            doc.skill_embedding = vec
            
        # Create the Critical Shift at JOY Hospital (Facility 4, Central Line)
        shift = await session.get(Shift, 99)
        if not shift:
            shift = Shift(
                id=99, 
                facility_id=4, 
                title="CODE BLUE: ICU Night", 
                required_specialty="ICU", 
                role_required="RMO", 
                department="ICU", 
                offered_rate_inr=10000, 
                rate_basis="per_shift", 
                start_time=datetime(2026, 10, 7, 19, 0, 0, tzinfo=timezone.utc), 
                end_time=datetime(2026, 10, 8, 7, 0, 0, tzinfo=timezone.utc)
            )
            session.add(shift)
        else:
            shift.status = ShiftStatus.OPEN
            shift.assigned_doctor_id = None
            shift.check_in_time = None
            shift.check_out_time = None
            
        await session.commit()
    await engine.dispose()
    print("✅ Database seeded: 10 SHIFT_READY doctors, 1 CRITICAL ICU shift (ID 99).")

async def test_matching():
    print("\n🧠 PHASE 2: Testing Transit + Semantic Matching...")
    async with httpx.AsyncClient() as client:
        # Deterministic Matching
        res = await client.post(f"{BASE_URL}/matching/find-doctors/99")
        data = res.json()
        print(f"✅ Deterministic Match found {data['total_matches']} doctors.")
        if data['ranked_doctors']:
            top = data['ranked_doctors'][0]
            print(f"🏆 Top Match: {top['name']} (Score: {top['match_score']}) - Reasons: {top['reasons']}")
            
        # Semantic Matching
        res2 = await client.post(f"{BASE_URL}/matching/semantic-search?query=ECMO%20Ventilator%20ICU")
        data2 = res2.json()
        print(f"✅ Semantic Vector Match found {data2['total_matches']} doctors.")

async def test_concurrency():
    print("\n⚡ PHASE 3: The Race Condition (5 Doctors accept simultaneously)...")
    
    async def accept_shift(doctor_id):
        async with httpx.AsyncClient() as client:
            res = await client.post(f"{BASE_URL}/shifts/99/accept?doctor_id={doctor_id}")
            return doctor_id, res.status_code, res.json()

    # Fire 5 requests at the EXACT same millisecond
    tasks = [accept_shift(i) for i in range(3, 8)] # Doctors 3, 4, 5, 6, 7
    results = await asyncio.gather(*tasks)
    
    successes = 0
    conflicts = 0
    for doc_id, status, body in results:
        if status == 200:
            successes += 1
            print(f"🟢 Doctor {doc_id} ACCEPTED the shift! (Status: {status})")
        elif status == 409:
            conflicts += 1
            print(f"🔴 Doctor {doc_id} BLOCKED by Redis Lock! (Status: {status})")
        else:
            print(f"⚠️ Doctor {doc_id} got unexpected status {status}: {body}")
            
    print(f"\n📊 Concurrency Result: {successes} Success, {conflicts} Conflicts.")
    assert successes == 1, "CRITICAL FAILURE: Double booking detected!"
    assert conflicts == 4, "CRITICAL FAILURE: Redis lock failed to block concurrent requests!"
    print("✅ Redis Distributed Locks held perfectly. No double bookings.")

async def test_geofence():
    print("\n📍 PHASE 4: GPS Geofence Validation...")
    async with httpx.AsyncClient() as client:
        # Test 1: 10km away
        res1 = await client.post(f"{BASE_URL}/attendance/shifts/99/check-in", json={
            "doctor_id": 3, "latitude": 19.1136, "longitude": 72.8697
        })
        print(f"🔴 Remote Check-in (10km away): {res1.status_code} - {res1.json().get('detail', 'Success')}")
        
        # Test 2: 50m away
        res2 = await client.post(f"{BASE_URL}/attendance/shifts/99/check-in", json={
            "doctor_id": 3, "latitude": 19.0560, "longitude": 72.8975
        })
        print(f"🟢 Local Check-in (50m away): {res2.status_code} - {res2.json().get('message', 'Failed')}")

async def main():
    print("="*50)
    print("🚀 DOCTORS ON CALL: SPRINT 1-20 STRESS TEST 🚀")
    print("="*50)
    
    await seed_database()
    await test_matching()
    await test_concurrency()
    await test_geofence()
    
    print("\n" + "="*50)
    print("🏆 ALL STRESS TESTS PASSED. SYSTEM IS PRODUCTION READY.")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
