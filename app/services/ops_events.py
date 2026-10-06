from datetime import datetime, timezone
from typing import Any

from app.services.event_bus import facility_channel, global_channel, publish_event


async def publish_ops_event(
    facility_id: int | None,
    event_type: str,
    payload: dict[str, Any],
    channel: str | None = None,
) -> dict[str, Any]:
    """
    Safely publish an operational event.

    This must never break the business transaction if Redis is unavailable.
    """
    try:
        if channel is None:
            channel = facility_channel(facility_id) if facility_id else global_channel()

        event = {
            "type": event_type,
            **payload,
        }

        if facility_id:
            event["facility_id"] = facility_id

        event["published_at"] = datetime.now(timezone.utc).isoformat()

        return await publish_event(channel, event)

    except Exception as exc:
        return {
            "published": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
