"""Merge provider snapshots without treating incomplete responses as deletion."""

import logging
from typing import Any

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from web.image_tasks import queue_event_image
from web.models import Event, Tag, TechGroup

logger = logging.getLogger(__name__)


def save_source_event(
    group: TechGroup,
    data: dict[str, Any],
    *,
    image_url: str = "",
    tags: list | None = None,
    location_complete: bool = False,
    synchronous_images: bool = False,
    existing_pk: int | None = None,
) -> tuple[Event | None, bool]:
    """Upsert within a group; omitted fields and unconfirmed empty locations survive."""
    values = dict(data)
    for key in ("start_datetime", "end_datetime"):
        if key not in values:
            continue
        value = values[key]
        if isinstance(value, str):
            try:
                value = parse_datetime(value)
            except ValueError:
                value = None
        if value is None or timezone.is_naive(value):
            values.pop(key)
        else:
            values[key] = value
    for key in ("name", "description", "url", "social_platform_id"):
        if not values.get(key):
            values.pop(key, None)
    if not location_complete:
        # Never mix a partial venue with an old venue's address/map.
        for key in ("location_name", "location_address", "map_link"):
            values.pop(key, None)
    for key, value in list(values.items()):
        field = Event._meta.get_field(key)
        if isinstance(value, str) and field.max_length:
            values[key] = value[: field.max_length]
    if not any(values.get(key) for key in ("name", "start_datetime", "status")):
        return None, False
    with transaction.atomic():
        # Serialize ingestion for a group, including first-time event creation.
        TechGroup.objects.select_for_update().get(pk=group.pk)
        candidates = Event.objects.select_for_update().filter(group=group)
        if existing_pk is not None:
            event = candidates.filter(pk=existing_pk).first()
            if event is None:
                return None, False
        elif values.get("social_platform_id"):
            event = candidates.filter(social_platform_id=values["social_platform_id"]).first()
        else:
            event = candidates.filter(name=values.get("name"), start_datetime=values.get("start_datetime")).first()
        is_new = event is None
        if event is None:
            if not values.get("name") or not values.get("start_datetime"):
                logger.warning("Skipping incomplete new event for group %s", group.pk)
                return None, False
            event = Event(group=group, location_name="", location_address="")
        if not is_new and any(
            getattr(event, key) != value
            for key, value in values.items()
            if key in {"name", "description", "location_name", "location_address", "url"}
        ):
            event.event_schema_verified = False
        for key, value in values.items():
            setattr(event, key, value)
        event.source_last_checked_at = timezone.now()
        event.save()
        if tags is not None:
            names = {
                " ".join(name.split())[: Tag._meta.get_field("value").max_length]
                for name in tags
                if isinstance(name, str) and name.strip()
            }
            obsolete = set(event.source_tag_names) - names
            if obsolete:
                event.tags.remove(*Tag.objects.filter(value__in=obsolete))
            for name in sorted(names):
                tag, _ = Tag.objects.get_or_create(value=name)
                event.tags.add(tag)
            Event.objects.filter(pk=event.pk).update(source_tag_names=sorted(names))
        queue_event_image(event, image_url, synchronous=synchronous_images)
    return event, is_new
