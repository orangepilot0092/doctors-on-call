from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from math import ceil
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dispute import Dispute
from app.models.doctor_master_record import Doctor
from app.models.facility import Facility
from app.models.shift import Shift, ShiftStatus
from app.services.matching_service import find_matching_doctors


URGENCY_WEIGHTS = {
    "ROUTINE": 1.0,
    "URGENT": 2.0,
    "HIGH": 2.0,
    "CRITICAL": 3.0,
}


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


def _urgency_weight(value: Any) -> float:
    return URGENCY_WEIGHTS.get(str(_enum_value(value)).upper(), 1.0)


def _utc_day_start(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _utc_day_end(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=timezone.utc)


def _date_from_dt(dt: datetime) -> date:
    return dt.astimezone(timezone.utc).date()


async def _get_facility_or_raise(db: AsyncSession, facility_id: int) -> Facility:
    facility = await db.get(Facility, facility_id)
    if not facility:
        raise LookupError("Facility not found")
    return facility


async def get_weekly_roster(
    db: AsyncSession,
    facility_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    facility = await _get_facility_or_raise(db, facility_id)

    today = start_date or datetime.now(timezone.utc).date()
    end = end_date or today + timedelta(days=6)

    if end < today:
        raise ValueError("end_date must be greater than or equal to start_date")

    start_dt = _utc_day_start(today)
    end_dt = _utc_day_end(end)

    shifts = (
        await db.execute(
            select(Shift)
            .where(
                Shift.facility_id == facility_id,
                Shift.start_time >= start_dt,
                Shift.start_time <= end_dt,
            )
            .order_by(Shift.start_time.asc())
        )
    ).scalars().all()

    doctor_ids = {s.assigned_doctor_id for s in shifts if s.assigned_doctor_id}
    doc_map: dict[int, Doctor] = {}

    if doctor_ids:
        docs = (
            await db.execute(
                select(Doctor).where(Doctor.id.in_(doctor_ids))
            )
        ).scalars().all()
        doc_map = {d.id: d for d in docs}

    roster_by_day: dict[str, list[dict]] = defaultdict(list)

    for s in shifts:
        day = _date_from_dt(s.start_time).isoformat()
        doc = doc_map.get(s.assigned_doctor_id) if s.assigned_doctor_id else None

        roster_by_day[day].append(
            {
                "shift_id": s.id,
                "title": s.title,
                "department": s.department or "GENERAL",
                "role_required": s.role_required,
                "required_specialty": s.required_specialty,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "status": _enum_value(s.status),
                "urgency_level": _enum_value(s.urgency_level),
                "offered_rate_inr": s.offered_rate_inr,
                "escrow_status": s.escrow_status,
                "assigned_doctor": (
                    {
                        "id": doc.id,
                        "doctor_code": doc.doctor_code,
                        "name": doc.full_name,
                        "trust_score": doc.trust_score,
                    }
                    if doc
                    else None
                ),
                "check_in_time": s.check_in_time.isoformat() if s.check_in_time else None,
                "check_out_time": s.check_out_time.isoformat() if s.check_out_time else None,
            }
        )

    total = len(shifts)
    filled = sum(1 for s in shifts if _enum_value(s.status) in {"ASSIGNED", "COMPLETED"})
    open_count = sum(1 for s in shifts if _enum_value(s.status) == "OPEN")
    critical_open = sum(
        1
        for s in shifts
        if _enum_value(s.status) == "OPEN"
        and _enum_value(s.urgency_level) == "CRITICAL"
    )

    return {
        "facility": {
            "id": facility.id,
            "name": facility.name,
            "transit_corridor": facility.transit_corridor,
        },
        "range": {
            "start_date": today.isoformat(),
            "end_date": end.isoformat(),
        },
        "summary": {
            "total_shifts": total,
            "filled_shifts": filled,
            "open_shifts": open_count,
            "critical_open_shifts": critical_open,
            "fill_rate_percent": round((filled / total * 100) if total else 0.0, 2),
        },
        "roster": dict(roster_by_day),
    }


async def get_staffing_gaps(
    db: AsyncSession,
    facility_id: int,
    days: int = 7,
    recommendations_per_shift: int = 3,
) -> dict:
    facility = await _get_facility_or_raise(db, facility_id)

    days = max(1, min(days, 30))
    recommendations_per_shift = max(1, min(recommendations_per_shift, 10))

    now = datetime.now(timezone.utc)
    start_dt = now
    end_dt = _utc_day_end(now.date() + timedelta(days=days - 1))

    open_shifts = (
        await db.execute(
            select(Shift)
            .where(
                Shift.facility_id == facility_id,
                Shift.status == ShiftStatus.OPEN,
                Shift.start_time >= start_dt,
                Shift.start_time <= end_dt,
            )
            .order_by(Shift.start_time.asc())
        )
    ).scalars().all()

    gaps = []

    for shift in open_shifts:
        try:
            matches = await find_matching_doctors(db, shift.id)
        except Exception:
            matches = []

        candidate_ids = [m["doctor_id"] for m in matches[: max(recommendations_per_shift * 3, 10)]]
        doc_map: dict[int, Doctor] = {}

        if candidate_ids:
            docs = (
                await db.execute(
                    select(Doctor).where(Doctor.id.in_(candidate_ids))
                )
            ).scalars().all()
            doc_map = {d.id: d for d in docs}

        recommended = []

        for m in matches:
            doc = doc_map.get(m["doctor_id"])
            trust_score = float(doc.trust_score or 0.0) if doc else 0.0
            match_score = float(m.get("match_score") or 0.0)
            combined_priority_score = match_score + (trust_score * 0.5)

            recommended.append(
                {
                    "doctor_id": m["doctor_id"],
                    "doctor_code": m.get("doctor_code"),
                    "name": m.get("name"),
                    "match_score": match_score,
                    "trust_score": doc.trust_score if doc else None,
                    "combined_priority_score": round(combined_priority_score, 2),
                    "reasons": m.get("reasons", []),
                    "specialty": m.get("specialty"),
                    "home_corridor": m.get("home_corridor"),
                }
            )

        recommended.sort(
            key=lambda x: x["combined_priority_score"],
            reverse=True,
        )

        gaps.append(
            {
                "shift_id": shift.id,
                "title": shift.title,
                "department": shift.department or "GENERAL",
                "role_required": shift.role_required,
                "required_specialty": shift.required_specialty,
                "urgency_level": _enum_value(shift.urgency_level),
                "start_time": shift.start_time.isoformat(),
                "end_time": shift.end_time.isoformat() if shift.end_time else None,
                "offered_rate_inr": shift.offered_rate_inr,
                "hours_until_start": round(
                    (shift.start_time - now).total_seconds() / 3600,
                    2,
                ),
                "recommended_doctors": recommended[:recommendations_per_shift],
            }
        )

    return {
        "facility": {
            "id": facility.id,
            "name": facility.name,
        },
        "window_days": days,
        "total_gaps": len(gaps),
        "gaps": gaps,
    }


async def get_hospital_metrics(
    db: AsyncSession,
    facility_id: int,
    days: int = 30,
) -> dict:
    facility = await _get_facility_or_raise(db, facility_id)

    days = max(1, min(days, 365))
    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(days=days)
    end_dt = now + timedelta(days=days)

    shifts = (
        await db.execute(
            select(Shift).where(
                Shift.facility_id == facility_id,
                Shift.start_time >= start_dt,
                Shift.start_time <= end_dt,
            )
        )
    ).scalars().all()

    status_counts: dict[str, int] = defaultdict(int)
    department_breakdown: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    financial_exposure = 0.0
    completed_value = 0.0

    for s in shifts:
        status = _enum_value(s.status) or "UNKNOWN"
        dept = s.department or "GENERAL"
        amount = float(s.offered_rate_inr or 0.0)

        status_counts[status] += 1
        department_breakdown[dept][status] += 1

        if status in {"OPEN", "ASSIGNED"}:
            financial_exposure += amount

        if status == "COMPLETED":
            completed_value += amount

    total = len(shifts)
    filled = status_counts.get("ASSIGNED", 0) + status_counts.get("COMPLETED", 0)
    completed_count = status_counts.get("COMPLETED", 0)

    no_show_disputes = (
        await db.execute(
            select(func.count(Dispute.id)).where(
                Dispute.hospital_id == facility_id,
                Dispute.dispute_type == "NO_SHOW",
            )
        )
    ).scalar() or 0

    open_disputes = (
        await db.execute(
            select(func.count(Dispute.id)).where(
                Dispute.hospital_id == facility_id,
                Dispute.status.in_(["OPEN", "UNDER_REVIEW"]),
            )
        )
    ).scalar() or 0

    refunded_disputes = (
        await db.execute(
            select(func.count(Dispute.id)).where(
                Dispute.hospital_id == facility_id,
                Dispute.status.in_(["REFUNDED", "PARTIAL_REFUND"]),
            )
        )
    ).scalar() or 0

    fill_rate = round((filled / total * 100) if total else 0.0, 2)
    no_show_rate = round((no_show_disputes / filled * 100) if filled else 0.0, 2)
    avg_completed_value = round(completed_value / completed_count, 2) if completed_count else 0.0

    return {
        "facility": {
            "id": facility.id,
            "name": facility.name,
        },
        "window_days": days,
        "total_shifts": total,
        "status_counts": dict(status_counts),
        "department_breakdown": {
            dept: dict(counts)
            for dept, counts in department_breakdown.items()
        },
        "fill_rate_percent": fill_rate,
        "no_show_disputes": no_show_disputes,
        "no_show_rate_percent": no_show_rate,
        "open_disputes": open_disputes,
        "refunded_disputes": refunded_disputes,
        "financial_exposure_inr": round(financial_exposure, 2),
        "completed_shift_value_inr": round(completed_value, 2),
        "average_completed_shift_value_inr": avg_completed_value,
    }


async def predict_staffing_heatmap(
    db: AsyncSession,
    facility_id: int,
    days: int = 7,
) -> dict:
    facility = await _get_facility_or_raise(db, facility_id)

    days = max(1, min(days, 30))
    historical_days = 28
    weeks = max(1, historical_days // 7)

    now = datetime.now(timezone.utc)
    hist_start = now - timedelta(days=historical_days)
    hist_end = now

    future_start = now
    future_end = _utc_day_end(now.date() + timedelta(days=days - 1))

    past_shifts = (
        await db.execute(
            select(Shift).where(
                Shift.facility_id == facility_id,
                Shift.start_time >= hist_start,
                Shift.start_time <= hist_end,
            )
        )
    ).scalars().all()

    future_shifts = (
        await db.execute(
            select(Shift).where(
                Shift.facility_id == facility_id,
                Shift.start_time >= future_start,
                Shift.start_time <= future_end,
            )
        )
    ).scalars().all()

    historical_counts: dict[tuple[int, str], float] = defaultdict(float)
    departments: set[str] = set()

    for s in past_shifts:
        wd = _date_from_dt(s.start_time).weekday()
        dept = s.department or "GENERAL"
        historical_counts[(wd, dept)] += 1
        departments.add(dept)

    future_by_day_dept: dict[str, dict[str, dict[str, float | int]]] = defaultdict(
        lambda: defaultdict(
            lambda: {
                "OPEN": 0,
                "ASSIGNED": 0,
                "COMPLETED": 0,
                "urgency_load": 0.0,
            }
        )
    )

    for s in future_shifts:
        d = _date_from_dt(s.start_time).isoformat()
        dept = s.department or "GENERAL"
        status = _enum_value(s.status) or "UNKNOWN"

        departments.add(dept)
        cell = future_by_day_dept[d][dept]

        if status in cell:
            cell[status] += 1

        if status == "OPEN":
            cell["urgency_load"] += _urgency_weight(s.urgency_level)

    heatmap = []

    for offset in range(days):
        dt = (now + timedelta(days=offset)).date()
        iso_date = dt.isoformat()
        weekday = dt.weekday()

        day_rows = []

        for dept in sorted(departments):
            expected = historical_counts.get((weekday, dept), 0.0) / weeks

            cell = future_by_day_dept.get(iso_date, {}).get(
                dept,
                {
                    "OPEN": 0,
                    "ASSIGNED": 0,
                    "COMPLETED": 0,
                    "urgency_load": 0.0,
                },
            )

            open_count = int(cell.get("OPEN", 0))
            assigned_count = int(cell.get("ASSIGNED", 0))
            urgency_load = float(cell.get("urgency_load", 0.0))

            if expected == 0:
                expected = float(open_count + assigned_count)

            projected_shortfall = max(0, ceil(expected - assigned_count))
            risk_score = min(
                100.0,
                (projected_shortfall * 20.0) + (urgency_load * 10.0),
            )

            if risk_score >= 70:
                risk_level = "HIGH"
            elif risk_score >= 40:
                risk_level = "MEDIUM"
            elif risk_score > 0:
                risk_level = "LOW"
            else:
                risk_level = "OK"

            day_rows.append(
                {
                    "department": dept,
                    "expected_demand": round(expected, 2),
                    "open_shifts": open_count,
                    "assigned_shifts": assigned_count,
                    "projected_shortfall": projected_shortfall,
                    "urgency_load": round(urgency_load, 2),
                    "risk_score": round(risk_score, 2),
                    "risk_level": risk_level,
                }
            )

        heatmap.append(
            {
                "date": iso_date,
                "weekday": dt.strftime("%A"),
                "departments": day_rows,
            }
        )

    attention_required = [
        {
            "date": day["date"],
            "weekday": day["weekday"],
            **row,
        }
        for day in heatmap
        for row in day["departments"]
        if row["risk_level"] in {"HIGH", "MEDIUM"} and row["projected_shortfall"] > 0
    ]

    return {
        "facility": {
            "id": facility.id,
            "name": facility.name,
        },
        "horizon_days": days,
        "historical_window_days": historical_days,
        "heatmap": heatmap,
        "attention_required": attention_required[:10],
    }


async def get_hospital_dashboard(
    db: AsyncSession,
    facility_id: int,
    days: int = 7,
) -> dict:
    days = max(1, min(days, 30))

    today = datetime.now(timezone.utc).date()
    end_date = today + timedelta(days=6)

    roster = await get_weekly_roster(db, facility_id, today, end_date)
    gaps = await get_staffing_gaps(db, facility_id, days=days, recommendations_per_shift=2)
    metrics = await get_hospital_metrics(db, facility_id, days=30)
    heatmap = await predict_staffing_heatmap(db, facility_id, days=days)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "facility": roster["facility"],
        "roster_summary": roster["summary"],
        "roster": roster["roster"],
        "staffing_gaps": gaps,
        "metrics": metrics,
        "predictive_heatmap": heatmap,
    }
