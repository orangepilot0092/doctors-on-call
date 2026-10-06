from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, nullslast

from app.db.session import get_db
from app.models.doctor_master_record import Doctor
from app.models.trust_snapshot import TrustSnapshot
from app.services.trust_service import TrustScoreService

router = APIRouter(prefix="/trust", tags=["Trust Score & Reputation"])


def _enum_value(value):
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


def _iso(value):
    return value.isoformat() if value else None


@router.post("/doctors/{doctor_id}/calculate")
async def calculate_trust_score(doctor_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await TrustScoreService.calculate_and_store(db, doctor_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"{type(exc).__name__}: {exc}")


@router.get("/doctors/{doctor_id}")
async def get_trust_profile(doctor_id: int, db: AsyncSession = Depends(get_db)):
    try:
        doctor = (
            await db.execute(select(Doctor).where(Doctor.id == doctor_id))
        ).scalar_one_or_none()

        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

        snapshot = (
            await db.execute(
                select(TrustSnapshot)
                .where(TrustSnapshot.doctor_id == doctor_id)
                .order_by(TrustSnapshot.calculated_at.desc())
                .limit(1)
            )
        ).scalars().first()

        return {
            "doctor_id": doctor.id,
            "doctor_code": doctor.doctor_code,
            "doctor_name": doctor.full_name,
            "status": _enum_value(doctor.status),
            "trust_score": doctor.trust_score,
            "completed_shift_count": doctor.completed_shift_count or 0,
            "no_show_count": doctor.no_show_count or 0,
            "late_check_in_count": doctor.late_check_in_count or 0,
            "last_trust_calculated_at": _iso(doctor.last_trust_calculated_at),
            "latest_snapshot": (
                {
                    "id": snapshot.id,
                    "score": snapshot.score,
                    "completed_shifts": snapshot.completed_shifts,
                    "no_shows": snapshot.no_shows,
                    "late_check_ins": snapshot.late_check_ins,
                    "open_disputes": snapshot.open_disputes,
                    "refunded_disputes": snapshot.refunded_disputes,
                    "verification_approved": snapshot.verification_approved,
                    "verification_rejected": snapshot.verification_rejected,
                    "explanation": snapshot.explanation,
                    "calculated_at": _iso(snapshot.calculated_at),
                }
                if snapshot
                else None
            ),
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Trust profile error: {type(exc).__name__}: {exc}"
        )


@router.get("/leaderboard")
async def trust_leaderboard(limit: int = 10, db: AsyncSession = Depends(get_db)):
    try:
        safe_limit = max(1, min(limit, 50))

        docs = (
            await db.execute(
                select(Doctor)
                .order_by(nullslast(Doctor.trust_score.desc()))
                .limit(safe_limit)
            )
        ).scalars().all()

        return {
            "leaderboard": [
                {
                    "doctor_id": d.id,
                    "doctor_code": d.doctor_code,
                    "doctor_name": d.full_name,
                    "status": _enum_value(d.status),
                    "trust_score": d.trust_score,
                    "completed_shift_count": d.completed_shift_count or 0,
                    "no_show_count": d.no_show_count or 0,
                    "late_check_in_count": d.late_check_in_count or 0,
                }
                for d in docs
            ]
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Trust leaderboard error: {type(exc).__name__}: {exc}"
        )
