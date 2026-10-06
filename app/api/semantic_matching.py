from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.db.session import get_db
from app.services.semantic_matching import find_doctors_by_skill, generate_mock_embedding
from app.models.doctor_master_record import Doctor

router = APIRouter(prefix="/matching", tags=["Semantic Matching"])

@router.post("/semantic-search")
async def semantic_search(query: str, db: AsyncSession = Depends(get_db)):
    matches = await find_doctors_by_skill(db, query)
    return {"query": query, "total_matches": len(matches), "ranked_doctors": matches}

@router.post("/seed-embeddings")
async def seed_embeddings(db: AsyncSession = Depends(get_db)):
    skills = {
        1: "Internal Medicine, Cardiology, Ventilator Management, ICU, Critical Care, ECMO",
        2: "Internal Medicine, General Ward, Diabetes Management, Outpatient, Routine Care"
    }
    for doc_id, text in skills.items():
        vec = generate_mock_embedding(text)
        stmt = update(Doctor).where(Doctor.id == doc_id).values(skill_embedding=vec)
        await db.execute(stmt)
    await db.commit()
    return {"message": "Mock vector embeddings seeded for Dr. Rohan and Dr. Anita"}
