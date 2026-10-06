import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.doctor_master_record import Doctor, DoctorStatus

async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Check if DOC-00001 exists
        from sqlalchemy import select
        result = await session.execute(select(Doctor).where(Doctor.doctor_code == "DOC-00001"))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("ℹ️ Test doctor DOC-00001 already exists.")
            return
            
        test_doc = Doctor(
            doctor_code="DOC-00001",
            full_name="Dr. Rohan Sharma",
            email="rohan.sharma.test@example.com",
            phone="9876543210",
            status=DoctorStatus.REGISTERED,
            mbbs_university="Grant Medical College (JJ Hospital)",
            mbbs_year=2018,
            pg_degree="MD",
            pg_specialty="Internal Medicine"
        )
        session.add(test_doc)
        await session.commit()
        print("✅ Successfully seeded test doctor: Dr. Rohan Sharma (DOC-00001)")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
