import json
from datetime import datetime, time, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.dispute import Dispute
from app.models.shift import Shift, ShiftStatus, UrgencyLevel
from app.services.event_bus import facility_channel, global_channel, publish_event, subscribe_events

router = APIRouter(prefix="/ops", tags=["Real-Time Operations"])


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


def _utc_day_start(d: datetime) -> datetime:
    return datetime.combine(d.date(), time.min, tzinfo=timezone.utc)


def _utc_day_end(d: datetime) -> datetime:
    return datetime.combine(d.date(), time.max, tzinfo=timezone.utc)


@router.get("/stream")
async def stream_ops_events(facility_id: int = Query(..., ge=0)):
    """
    Server-Sent Events stream for a facility's live operations channel.
    """
    channel = facility_channel(facility_id) if facility_id > 0 else global_channel()

    async def event_generator():
        try:
            async for raw_event in subscribe_events(channel):
                yield f"data: {raw_event}\n\n"
        except Exception as exc:
            error_payload = {
                "channel": channel,
                "event": {
                    "type": "STREAM_ERROR",
                    "error": f"{type(exc).__name__}: {exc}",
                },
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/events/emit")
async def emit_ops_event(
    facility_id: int = Query(..., ge=0),
    event: dict[str, Any] = ...,
):
    """
    Test/manual event emitter for the live ops stream.
    In production, business services will publish these events automatically.
    """
    channel = facility_channel(facility_id) if facility_id > 0 else global_channel()
    enriched = {
        **event,
        "facility_id": facility_id,
        "published_at": datetime.now(timezone.utc).isoformat(),
    }
    published = await publish_event(channel, enriched)
    return {
        "published": True,
        "channel": channel,
        "event": published,
    }


@router.get("/board")
async def live_ops_board(
    facility_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
):
    """
    Snapshot of the current live operations board for a facility.
    """
    now = datetime.now(timezone.utc)
    today_start = _utc_day_start(now)
    today_end = _utc_day_end(now)
    horizon_end = _utc_day_end(now + timedelta(days=7))

    open_count = (
        await db.execute(
            select(func.count(Shift.id)).where(
                Shift.facility_id == facility_id,
                Shift.status == ShiftStatus.OPEN,
            )
        )
    ).scalar() or 0

    critical_open_count = (
        await db.execute(
            select(func.count(Shift.id)).where(
                Shift.facility_id == facility_id,
                Shift.status == ShiftStatus.OPEN,
                Shift.urgency_level == UrgencyLevel.CRITICAL,
            )
        )
    ).scalar() or 0

    high_open_count = (
        await db.execute(
            select(func.count(Shift.id)).where(
                Shift.facility_id == facility_id,
                Shift.status == ShiftStatus.OPEN,
                Shift.urgency_level == UrgencyLevel.HIGH,
            )
        )
    ).scalar() or 0

    assigned_today = (
        await db.execute(
            select(func.count(Shift.id)).where(
                Shift.facility_id == facility_id,
                Shift.status == ShiftStatus.ASSIGNED,
                Shift.start_time >= today_start,
                Shift.start_time <= today_end,
            )
        )
    ).scalar() or 0

    completed_today = (
        await db.execute(
            select(func.count(Shift.id)).where(
                Shift.facility_id == facility_id,
                Shift.status == ShiftStatus.COMPLETED,
                Shift.start_time >= today_start,
                Shift.start_time <= today_end,
            )
        )
    ).scalar() or 0

    upcoming_open = (
        await db.execute(
            select(func.count(Shift.id)).where(
                Shift.facility_id == facility_id,
                Shift.status == ShiftStatus.OPEN,
                Shift.start_time >= now,
                Shift.start_time <= horizon_end,
            )
        )
    ).scalar() or 0

    escrow_held_value = (
        await db.execute(
            select(func.coalesce(func.sum(Shift.offered_rate_inr), 0)).where(
                Shift.facility_id == facility_id,
                Shift.escrow_status == "HELD",
            )
        )
    ).scalar() or 0

    financial_exposure = (
        await db.execute(
            select(func.coalesce(func.sum(Shift.offered_rate_inr), 0)).where(
                Shift.facility_id == facility_id,
                Shift.status.in_([ShiftStatus.OPEN, ShiftStatus.ASSIGNED]),
            )
        )
    ).scalar() or 0

    recent_disputes = (
        await db.execute(
            select(
                Dispute.id,
                Dispute.shift_id,
                Dispute.dispute_type,
                Dispute.status,
                Dispute.amount_claimed,
                Dispute.amount_refunded,
                Dispute.created_at,
                Dispute.resolved_at,
            )
            .where(Dispute.hospital_id == facility_id)
            .order_by(Dispute.created_at.desc())
            .limit(5)
        )
    ).all()

    return {
        "facility_id": facility_id,
        "generated_at": now.isoformat(),
        "live_board": {
            "open_shifts": open_count,
            "critical_open_shifts": critical_open_count,
            "high_open_shifts": high_open_count,
            "assigned_today": assigned_today,
            "completed_today": completed_today,
            "upcoming_open_7_days": upcoming_open,
            "escrow_held_value_inr": float(escrow_held_value or 0),
            "financial_exposure_inr": float(financial_exposure or 0),
        },
        "recent_disputes": [
            {
                "dispute_id": row.id,
                "shift_id": row.shift_id,
                "type": row.dispute_type,
                "status": row.status,
                "amount_claimed": row.amount_claimed,
                "amount_refunded": row.amount_refunded,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
            }
            for row in recent_disputes
        ],
    }
