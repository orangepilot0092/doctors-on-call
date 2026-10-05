from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.shift import Shift
from app.schemas.shift import ShiftCreate
from typing import List

async def create_shift(db: AsyncSession, shift_data: ShiftCreate) -> Shift:
    new_shift = Shift(**shift_data.model_dump())
    db.add(new_shift)
    await db.commit()
    await db.refresh(new_shift)
    return new_shift

async def get_shifts(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Shift]:
    result = await db.execute(select(Shift).offset(skip).limit(limit))
    return result.scalars().all()

async def get_shift_by_id(db: AsyncSession, shift_id: int) -> Shift:
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    return result.scalar_one_or_none()
