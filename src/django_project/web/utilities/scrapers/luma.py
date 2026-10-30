"""Read the publicly advertised Luma calendar iCal subscription.

The feed provides factual event metadata only; it does not identify the
BuildCities network that may have republished an event.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urlsplit

import requests
from icalendar import Calendar

logger = logging.getLogger(__name__)

_MAX_FEED_BYTES = 5_000_000
_EVENT_LINK = re.compile(r"https?://(?:www\.)?(?:luma\.com|lu\.ma)/[\w-]+", re.IGNORECASE)
_CDA_LOCATION = re.compile(r"\bCoeur d['’]Alene\b\s*,\s*(?:ID|Idaho)\b", re.IGNORECASE)


def validate_calendar_url(url: str) -> None:
    """Allow only the calendar-scoped subscription endpoint, never arbitrary hosts."""
    parts = urlsplit(url)
    params = parse_qs(parts.query, strict_parsing=True)
    if (
        parts.scheme != "https"
        or parts.netloc != "api.luma.com"
        or parts.path != "/ics/get"
        or parts.fragment
        or set(params) != {"entity", "id"}
        or params.get("entity") != ["calendar"]
        or len(params.get("id", [])) != 1
        or not re.fullmatch(r"cal-[A-Za-z0-9]+", params["id"][0])
    ):
        raise ValueError("Expected a public Luma calendar subscription URL")


def fetch_luma_calendar(url: str) -> bytes:
    """Fetch a bounded public feed with a finite timeout."""
    validate_calendar_url(url)
    response = requests.get(url, headers={"Accept": "text/calendar"}, timeout=20, stream=True, allow_redirects=False)
    try:
        if response.status_code in range(300, 400):
            raise ValueError("Unexpected Luma calendar redirect")
        response.raise_for_status()
        result = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            result.extend(chunk)
            if len(result) > _MAX_FEED_BYTES:
                raise ValueError("Luma calendar exceeds maximum supported size")
        return bytes(result)
    finally:
        response.close()


def normalize_event_url(url: str) -> str | None:
    """Only accept an individual public Luma registration permalink."""
    parts = urlsplit(url.strip())
    if (
        parts.scheme != "https"
        or parts.netloc.lower() not in {"luma.com", "www.luma.com", "lu.ma", "www.lu.ma"}
        or not re.fullmatch(r"/[a-zA-Z0-9_-]+/?", parts.path)
        or parts.path.rstrip("/") in {"", "/event"}
        or parts.query
        or parts.fragment
    ):
        return None
    return f"https://luma.com{parts.path.rstrip('/')}"


def is_coeur_dalene_location(value: str) -> bool:
    """Require an explicit Idaho city and a physical street-address field."""
    return bool(_CDA_LOCATION.search(value) and re.search(r"\b\d{1,6}\s+\S+", value))


def _valid_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None:
        return value
    return None


def parse_luma_calendar(content: bytes) -> list[dict[str, Any]]:
    """Convert VEVENTs into conservative, factual source snapshots.

    Malformed/incomplete VEVENTs are skipped, not treated as deleted events.
    An empty valid calendar remains empty; the caller must never reconcile
    missing entries into cancellations.
    """
    calendar = Calendar.from_ical(content)
    if calendar.name != "VCALENDAR":
        raise ValueError("Luma response is not a VCALENDAR")
    events: list[dict[str, Any]] = []
    seen_uids: set[str] = set()
    for component in calendar.walk("VEVENT"):
        uid = str(component.get("UID", "")).strip()
        name = str(component.get("SUMMARY", "")).strip()
        start_field = component.get("DTSTART")
        end_field = component.get("DTEND")
        start = _valid_datetime(start_field.dt) if start_field is not None else None
        end = _valid_datetime(end_field.dt) if end_field is not None else None
        if not uid or not name or not start or (end and end <= start):
            logger.warning("Skipping incomplete Luma VEVENT with UID %s", uid)
            continue
        if uid in seen_uids:
            raise ValueError("Duplicate Luma event UID in calendar")
        seen_uids.add(uid)
        description = str(component.get("DESCRIPTION", ""))
        candidates = _EVENT_LINK.findall(description)
        url = next((clean for raw in candidates if (clean := normalize_event_url(raw))), None)
        if not url:
            logger.warning("Skipping Luma event %s without a public event URL", uid)
            continue
        location = str(component.get("LOCATION", "")).strip()
        venue = location.split(",", maxsplit=1)[0].strip()
        complete = bool(location and re.search(r"\b\d{1,6}\s+\S+", location) and "," in location)
        events.append(
            {
                "social_platform_id": uid,
                "name": name,
                "start_datetime": start,
                **({"end_datetime": end} if end else {}),
                "url": url,
                "location_name": venue,
                "location_address": location,
                "location_complete": complete,
                # An independent, brief summary; never reproduce Luma page descriptions.
                "description": "See Luma for event details and registration.",
            }
        )
    return events
