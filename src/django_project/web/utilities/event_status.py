"""Normalize only explicit provider lifecycle evidence."""

from typing import Any


def source_event_status(data: dict[str, Any]) -> str | None:
    for key in ("isCanceled", "isCancelled", "is_cancelled", "is_canceled"):
        if data.get(key) is True:
            return "cancelled"
    for key in ("eventStatus", "status"):
        value = data.get(key)
        if not isinstance(value, str):
            continue
        value = value.rstrip("/").rsplit("/", 1)[-1].casefold()
        if value in {"cancelled", "canceled", "eventcancelled"}:
            return "cancelled"
        if value in {
            "active",
            "live",
            "published",
            "upcoming",
            "scheduled",
            "eventscheduled",
            "started",
            "ended",
            "past",
            "completed",
        }:
            return "active"
    return None
