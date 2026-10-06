from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.hospital_rostering_service import (
    get_hospital_dashboard,
    get_hospital_metrics,
    get_staffing_gaps,
    get_weekly_roster,
    predict_staffing_heatmap,
)

router = APIRouter(prefix="/hospitals", tags=["Hospital Rostering & Predictive Staffing"])


@router.get("/{facility_id}/roster")
async def roster(
    facility_id: int,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_weekly_roster(db, facility_id, start_date, end_date)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Roster error: {type(exc).__name__}: {exc}",
        )


@router.get("/{facility_id}/staffing-gaps")
async def staffing_gaps(
    facility_id: int,
    days: int = Query(7, ge=1, le=30),
    recommendations_per_shift: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_staffing_gaps(db, facility_id, days, recommendations_per_shift)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Staffing gap error: {type(exc).__name__}: {exc}",
        )


@router.get("/{facility_id}/metrics")
async def metrics(
    facility_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_hospital_metrics(db, facility_id, days)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Metrics error: {type(exc).__name__}: {exc}",
        )


@router.get("/{facility_id}/predictive-heatmap")
async def predictive_heatmap(
    facility_id: int,
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await predict_staffing_heatmap(db, facility_id, days)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Heatmap error: {type(exc).__name__}: {exc}",
        )


@router.get("/{facility_id}/dashboard")
async def dashboard(
    facility_id: int,
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_hospital_dashboard(db, facility_id, days)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Dashboard error: {type(exc).__name__}: {exc}",
        )
