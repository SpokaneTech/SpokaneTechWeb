"""Retryable provider image ingestion, independent of event metadata ingestion."""

import logging
from uuid import uuid4

import requests
from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction

from web.models import Event
from web.utilities.event_images import ImageDownloadError, download_event_image, validate_image_url

logger = logging.getLogger(__name__)


def queue_event_image(event: Event, source_url: str, *, synchronous: bool = False) -> None:
    if not source_url:
        return
    try:
        validate_image_url(source_url)
    except ValueError:
        logger.warning("Ignoring unsupported image URL for event %s", event.pk)
        return
    # An uploaded image, or one replaced in admin, belongs to the editor.
    if event.image and event.image.name != event.image_managed_name:
        return
    Event.objects.filter(pk=event.pk).update(image_source_url=source_url)
    if event.image and event.image_synced_url == source_url and event.image.storage.exists(event.image.name):
        return

    def download_after_commit() -> None:
        if synchronous:
            result = ingest_event_image.apply(args=(event.pk, source_url), throw=False)
            if result.failed():
                logger.error("Image download failed for event %s: %s", event.pk, type(result.result).__name__)
            else:
                logger.info("Image ingestion for event %s: %s", event.pk, result.result)
        else:
            ingest_event_image.delay(event.pk, source_url)

    transaction.on_commit(download_after_commit)


@shared_task(
    name="web.ingest_event_image",
    autoretry_for=(requests.RequestException, OSError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    time_limit=120,
)
def ingest_event_image(event_pk: int, source_url: str) -> str:
    event = Event.objects.filter(pk=event_pk).first()
    if event is None or event.image_source_url != source_url:
        return "Image job is obsolete."
    if event.image and event.image.name != event.image_managed_name:
        return "Preserving manually uploaded image."
    if event.image and event.image_synced_url == source_url and event.image.storage.exists(event.image.name):
        return "Event image is unchanged."
    try:
        content = download_event_image(source_url)
    except ImageDownloadError as exc:
        logger.warning("Rejected image for event %s: %s", event_pk, exc)
        return "Image rejected; existing image retained."

    with transaction.atomic():
        event = Event.objects.select_for_update().get(pk=event_pk)
        if event.image_source_url != source_url or (event.image and event.image.name != event.image_managed_name):
            return "Image changed while downloading; leaving it intact."
        if event.image and event.image_synced_url == source_url and event.image.storage.exists(event.image.name):
            return "Event image is unchanged."
        old_name = event.image_managed_name
        storage = event.image.storage
        event.image.save(f"{event.pk}-{uuid4().hex}.webp", ContentFile(content), save=False)
        new_name = event.image.name
        try:
            Event.objects.filter(pk=event.pk).update(
                image=new_name, image_synced_url=source_url, image_managed_name=new_name
            )
        except Exception:
            storage.delete(new_name)
            raise
        if old_name and old_name != new_name:
            transaction.on_commit(lambda: storage.delete(old_name))
    return "Event image saved."
