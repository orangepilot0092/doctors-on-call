import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.doctor_master_record import Doctor

def generate_mock_embedding(text: str, dimensions: int = 1536) -> list[float]:
    np.random.seed(hash(text) % 2**32)
    vec = np.random.rand(dimensions).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()

async def find_doctors_by_skill(db: AsyncSession, skill_query: str, limit: int = 5) -> list[dict]:
    query_vec = generate_mock_embedding(skill_query)
    stmt = (
        select(Doctor.id, Doctor.doctor_code, Doctor.full_name, Doctor.pg_specialty)
        .where(Doctor.skill_embedding.isnot(None))
        .order_by(Doctor.skill_embedding.cosine_distance(query_vec))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [dict(row._mapping) for row in result.all()]
